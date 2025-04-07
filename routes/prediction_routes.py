from flask import Blueprint, jsonify
from scapy.all import sniff, IP, TCP, conf
import csv
import os
import threading
from datetime import datetime
from collections import deque

prediction_routes = Blueprint('prediction_routes', __name__)

# Global variables
is_monitoring = False
csv_file = 'network_traffic_features.csv'
packet_queue = deque(maxlen=100)  # Stores last 100 packets for display
capture_thread = None

fieldnames = [
    'timestamp', 'source_ip', 'destination_ip', 'avg_bwd_segment_size', 
    'bwd_packet_length_mean', 'init_win_bytes_forward', 'fwd_iat_max', 
    'fwd_iat_total', 'max_packet_length', 'bwd_packet_length_max', 
    'bwd_packet_length_std', 'bwd_iat_max', 'init_win_bytes_backward', 
    'bwd_iat_total'
]

def select_network_interface():
    """Select the most appropriate network interface"""
    print("Available network interfaces:")
    for iface in conf.ifaces:
        print(f"{iface}: {conf.ifaces[iface].name}")
    
    for iface in conf.ifaces:
        iface_name = conf.ifaces[iface].name
        if 'Ethernet' in iface_name or 'Wi-Fi' in iface_name:
            print(f"Selected interface: {iface_name}")
            return iface_name
    return None

def process_packet(packet):
    """Process each captured packet and extract features"""
    if IP in packet:
        row = {
            'timestamp': datetime.now().isoformat(),
            'source_ip': packet[IP].src,
            'destination_ip': packet[IP].dst,
            'avg_bwd_segment_size': None,
            'bwd_packet_length_mean': None,
            'init_win_bytes_forward': None,
            'fwd_iat_max': None,
            'fwd_iat_total': None,
            'max_packet_length': None,
            'bwd_packet_length_max': None,
            'bwd_packet_length_std': None,
            'bwd_iat_max': None,
            'init_win_bytes_backward': None,
            'bwd_iat_total': None
        }

        if TCP in packet:
            row['max_packet_length'] = len(packet)
            if 'window' in packet[TCP].fields:
                row['init_win_bytes_forward'] = packet[TCP].window

        packet_queue.append(row)
        
        # Write to CSV if we have basic packet info
        if all(row[k] is not None for k in ['timestamp', 'source_ip', 'destination_ip', 'max_packet_length']):
            try:
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow(row)
            except Exception as e:
                print(f"Error writing to CSV: {str(e)}")
        
        return row
    return None

@prediction_routes.route('/get_packets')
def get_packets():
    """Endpoint to get recent packets for display"""
    return jsonify({
        'packets': list(packet_queue),
        'count': len(packet_queue)
    })

def start_sniffing():
    """Start packet capture on selected interface"""
    try:
        # Initialize CSV file
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

        # Select network interface
        iface = select_network_interface()
        if iface:
            print(f"Starting capture on interface {iface}")
            sniff(prn=process_packet, store=False, stop_filter=lambda x: not is_monitoring, iface=iface)
        else:
            print("No suitable network interface found")
    except Exception as e:
        print(f"Capture error: {str(e)}")

@prediction_routes.route('/start_capture', methods=['POST'])
def start_capture():
    global is_monitoring, capture_thread
    
    if is_monitoring:
        return jsonify({'error': 'Capture already running'}), 400
    
    is_monitoring = True
    packet_queue.clear()
    
    # Start capture in a new thread
    capture_thread = threading.Thread(target=start_sniffing)
    capture_thread.start()
    
    return jsonify({
        'status': 'Capture started',
        'output_file': os.path.abspath(csv_file),
        'message': f"Capturing network traffic to {csv_file}"
    })

@prediction_routes.route('/stop_capture', methods=['POST'])
def stop_capture():
    global is_monitoring
    
    if not is_monitoring:
        return jsonify({'error': 'No capture running'}), 400
    
    is_monitoring = False
    
    # Wait for thread to finish
    if capture_thread and capture_thread.is_alive():
        capture_thread.join(timeout=5)
    
    return jsonify({
        'status': 'Capture stopped',
        'output_file': os.path.abspath(csv_file),
        'count': len(packet_queue),
        'message': f"Capture stopped. {len(packet_queue)} packets captured"
    })