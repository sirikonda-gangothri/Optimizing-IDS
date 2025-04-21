from flask import Blueprint, jsonify, request, render_template, send_file
from scapy.all import sniff, IP, TCP, conf
import csv
import os
import threading
from datetime import datetime
from collections import deque
import pickle
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import joblib
import tempfile
import shutil
import sklearn
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

traffic = Blueprint('traffic', __name__)

# Global variables
is_monitoring = False
csv_file = 'network_traffic_features.csv'
packet_queue = deque(maxlen=1000)
prediction_queue = deque(maxlen=100)
capture_thread = None
loaded_model = None
model_loaded = False
graph_data = deque(maxlen=50)
model_classes = ['Benign', 'DDoS']  # Default class labels

def select_network_interface():
    """Select the most appropriate network interface"""
    for iface in conf.ifaces:
        iface_name = conf.ifaces[iface].name
        if 'Ethernet' in iface_name or 'Wi-Fi' in iface_name or 'eth' in iface_name.lower():
            return iface_name
    return conf.ifaces.dev_from_index(0).name if conf.ifaces else None

def predict_traffic(packet_features):
    """Predict traffic type using loaded model and return prediction with confidence"""
    if not model_loaded or loaded_model is None:
        return "No model loaded", 0.0
    
    try:
        # Prepare features in the order expected by the model
        features = []
        if hasattr(loaded_model, 'feature_names_in_'):
            # If model has feature names, use them to order the features
            for feature_name in loaded_model.feature_names_in_:
                features.append(packet_features.get(feature_name, 0))
        else:
            # Fallback to using all available features in packet_features
            for key in packet_features:
                if key not in ['timestamp', 'source_ip', 'destination_ip', 'prediction', 'confidence']:
                    features.append(packet_features[key])
        
        features_array = np.array(features).reshape(1, -1)
        
        # Get prediction
        prediction = loaded_model.predict(features_array)[0]
        
        # Get confidence scores if available
        confidence = 0.0
        if hasattr(loaded_model, 'predict_proba'):
            proba = loaded_model.predict_proba(features_array)[0]
            confidence = max(proba)  # Use the highest class probability
        elif hasattr(loaded_model, 'decision_function'):
            decision = loaded_model.decision_function(features_array)[0]
            confidence = float(abs(decision))  # Use absolute value of decision function
        
        # Use model's classes if available
        if hasattr(loaded_model, 'classes_'):
            try:
                predicted_label = loaded_model.classes_[prediction]
            except IndexError:
                predicted_label = str(prediction)
        else:
            # Default to our class labels
            predicted_label = model_classes[prediction] if prediction < len(model_classes) else str(prediction)
        
        return predicted_label, confidence
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return "Prediction error", 0.0

def generate_graph():
    """Generate visualization graph showing Benign vs DDoS traffic"""
    if not graph_data:
        return None
    
    plt.figure(figsize=(12, 6))
    timestamps = [d['timestamp'] for d in graph_data]
    lengths = [d['length'] for d in graph_data]
    predictions = [d['prediction'] for d in graph_data]
    confidences = [d['confidence'] for d in graph_data]
    
    try:
        times = [datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f") for ts in timestamps]
    except ValueError:
        times = [datetime.strptime(ts.split('.')[0], "%Y-%m-%dT%H:%M:%S") for ts in timestamps]
    
    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot packet sizes with color based on prediction
    colors = []
    for pred in predictions:
        if 'DDoS' in str(pred):
            colors.append('red')
        else:
            colors.append('green')
    
    ax1.scatter(times, lengths, c=colors, alpha=0.6, label='Packet Size')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Packet Size (bytes)')
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # Create secondary axis for confidence
    ax2 = ax1.twinx()
    
    # Plot confidence scores
    ax2.plot(times, confidences, 'b-', alpha=0.4, label='Confidence')
    ax2.set_ylabel('Confidence Score', color='b')
    ax2.tick_params('y', colors='b')
    ax2.set_ylim(0, 1.1)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Add title
    plt.title('Network Traffic Analysis - Benign (Green) vs DDoS (Red)')
    
    # Add horizontal lines for thresholds
    ax1.axhline(y=1500, color='orange', linestyle='--', alpha=0.3, label='Jumbo Frame Threshold')
    
    # Tight layout
    fig.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    
    return base64.b64encode(buf.read()).decode('utf-8')

def process_packet(packet):
    """Process each captured packet and extract features"""
    if IP in packet:
        # Initialize with basic features we can always extract
        row = {
            'timestamp': datetime.now().isoformat(),
            'source_ip': packet[IP].src,
            'destination_ip': packet[IP].dst,
            'packet_length': len(packet),
            'protocol': packet[IP].proto,
        }
        
        # Add TCP-specific features if available
        if TCP in packet:
            row.update({
                'src_port': packet[TCP].sport,
                'dst_port': packet[TCP].dport,
                'window_size': packet[TCP].window,
                'flags': packet[TCP].flags
            })
        
        if model_loaded:
            # Get prediction and confidence
            prediction, confidence = predict_traffic(row)
            row['prediction'] = prediction
            row['confidence'] = confidence
        else:
            row['prediction'] = "No model"
            row['confidence'] = 0.0
        
        # Add to queues
        packet_queue.append(row)
        prediction_queue.append(row)
        
        # Add to graph data
        graph_data.append({
            'timestamp': row['timestamp'],
            'length': row['packet_length'],
            'prediction': row['prediction'],
            'confidence': row['confidence']
        })
        
        # Write to CSV
        try:
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, 'a', newline='') as f:
                # Dynamically get fieldnames from the row keys
                writer = csv.DictWriter(f, fieldnames=row.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
        except Exception as e:
            logger.error(f"Error writing to CSV: {str(e)}")
        
        return row
    return None

@traffic.route('/get_predictions')
def get_predictions():
    """Endpoint to get recent predictions for display"""
    return jsonify({
        'predictions': list(prediction_queue)[-100:],
        'count': len(prediction_queue),
        'graph': generate_graph()
    })

def start_sniffing():
    """Start packet capture on selected interface"""
    global is_monitoring
    
    try:
        iface = select_network_interface()
        if iface:
            logger.info(f"Starting capture on interface {iface}")
            sniff(prn=process_packet, store=False, stop_filter=lambda x: not is_monitoring, iface=iface)
        else:
            logger.error("No suitable network interface found")
    except Exception as e:
        logger.error(f"Capture error: {str(e)}")
    finally:
        is_monitoring = False

@traffic.route('/start_capture', methods=['POST'])
def start_capture():
    global is_monitoring, capture_thread
    
    if is_monitoring:
        return jsonify({'error': 'Capture already running'}), 400
    
    if not model_loaded:
        return jsonify({'error': 'No model loaded'}), 400
    
    is_monitoring = True
    packet_queue.clear()
    prediction_queue.clear()
    graph_data.clear()
    
    capture_thread = threading.Thread(target=start_sniffing)
    capture_thread.daemon = True
    capture_thread.start()
    
    return jsonify({
        'status': 'Capture started',
        'output_file': os.path.abspath(csv_file),
        'message': f"Capturing network traffic to {csv_file}"
    })

@traffic.route('/stop_capture', methods=['POST'])
def stop_capture():
    global is_monitoring
    
    if not is_monitoring:
        return jsonify({'error': 'No capture running'}), 400
    
    is_monitoring = False
    
    if capture_thread and capture_thread.is_alive():
        capture_thread.join(timeout=5)
    
    return jsonify({
        'status': 'Capture stopped',
        'output_file': os.path.abspath(csv_file),
        'count': len(prediction_queue),
        'message': f"Capture stopped. {len(prediction_queue)} packets analyzed"
    })

@traffic.route('/load_model', methods=['POST'])
def load_model():
    global loaded_model, model_loaded, model_classes
    
    if 'model' not in request.files:
        logger.error("No file part in request")
        return jsonify({'error': 'No file uploaded'}), 400
    
    model_file = request.files['model']
    
    if not model_file or model_file.filename == '':
        logger.error("No selected file")
        return jsonify({'error': 'No selected file'}), 400
        
    if not (model_file.filename.lower().endswith('.pkl') or 
            model_file.filename.lower().endswith('.joblib') or
            model_file.filename.lower().endswith('.sav')):
        logger.error(f"Invalid file type: {model_file.filename}")
        return jsonify({'error': 'Invalid file type. Please upload a .pkl, .joblib or .sav file'}), 400
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, model_file.filename)
            model_file.save(temp_path)
            logger.info(f"Saved uploaded file to {temp_path}")
            
            logger.info(f"Current scikit-learn version: {sklearn.__version__}")
            
            try:
                loaded_model = joblib.load(temp_path)
                logger.info("Model loaded successfully with joblib")
            except Exception as joblib_error:
                logger.warning(f"Joblib load failed: {str(joblib_error)}. Falling back to pickle.")
                try:
                    with open(temp_path, 'rb') as f:
                        loaded_model = pickle.load(f)
                    logger.info("Model loaded successfully with pickle")
                except Exception as pickle_error:
                    error_msg = (
                        f"Failed to load model.\n"
                        f"Joblib error: {str(joblib_error)}\n"
                        f"Pickle error: {str(pickle_error)}\n"
                        f"Current scikit-learn version: {sklearn.__version__}\n"
                        f"Ensure the model was trained with a compatible scikit-learn version."
                    )
                    logger.error(error_msg)
                    return jsonify({'error': error_msg}), 400
            
            if not hasattr(loaded_model, 'predict'):
                error_msg = "Uploaded file is not a valid scikit-learn model (missing predict method)"
                logger.error(error_msg)
                return jsonify({'error': error_msg}), 400
            
            # Get model's class labels if available
            if hasattr(loaded_model, 'classes_'):
                model_classes = loaded_model.classes_.tolist()
                logger.info(f"Model classes: {model_classes}")
            
            # Test prediction with dummy data
            try:
                if hasattr(loaded_model, 'feature_names_in_'):
                    dummy_features = {name: 0 for name in loaded_model.feature_names_in_}
                else:
                    # Create dummy features with typical network traffic features
                    dummy_features = {
                        'packet_length': 0,
                        'src_port': 0,
                        'dst_port': 0,
                        'window_size': 0,
                        'protocol': 0
                    }
                
                # Test prediction
                prediction, confidence = predict_traffic(dummy_features)
                logger.info(f"Test prediction: {prediction} (confidence: {confidence})")
            except Exception as e:
                error_msg = f"Model test failed: {str(e)}"
                logger.error(error_msg)
                return jsonify({'error': error_msg}), 400
        
        model_loaded = True
        logger.info(f"Model loaded successfully: {type(loaded_model).__name__}")
        
        return jsonify({
            'status': 'Model loaded successfully',
            'model_type': str(type(loaded_model).__name__),
            'features': loaded_model.feature_names_in_.tolist() if hasattr(loaded_model, 'feature_names_in_') else 'Unknown',
            'classes': model_classes,
            'sklearn_version': sklearn.__version__
        })
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return jsonify({
            'error': f'Error loading model: {str(e)}',
            'advice': (
                'Ensure the file is a valid scikit-learn model saved with joblib or pickle. '
                f'Current scikit-learn version: {sklearn.__version__}. '
                'Check if the model was trained with a compatible version.'
            )
        }), 500

@traffic.route('/')
def traffic_monitoring():
    return render_template('traffic.html')

@traffic.route('/download_csv')
def download_csv():
    if not os.path.exists(csv_file):
        logger.error("CSV file not found")
        return jsonify({'error': 'No data file available'}), 404
    
    try:
        return send_file(
            csv_file,
            as_attachment=True,
            download_name='network_traffic_analysis.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        logger.error(f"Error sending CSV file: {str(e)}")
        return jsonify({'error': str(e)}), 500