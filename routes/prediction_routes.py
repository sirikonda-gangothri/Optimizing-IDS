from flask import Blueprint, jsonify
from scapy.all import sniff, IP, TCP, conf
import csv
import os
import threading
from datetime import datetime

prediction_routes = Blueprint('prediction_routes', __name__)

# Global variables
is_monitoring = False
csv_file = 'network_traffic_features.csv'

# List of desired feature names
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
    
    # Prefer Ethernet or Wi-Fi interfaces
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

        # Write to CSV if all required fields are present
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if all(value is not None for value in row.values()):
                writer.writerow(row)

def start_sniffing():
    """Start packet capture on selected interface"""
    # Initialize CSV file
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    # Select network interface
    iface = select_network_interface()
    if iface:
        sniff(prn=process_packet, store=False, stop_filter=lambda x: not is_monitoring, iface=iface)
    else:
        print("No suitable network interface found")

@prediction_routes.route('/start_capture', methods=['POST'])
def start_capture():
    global is_monitoring
    is_monitoring = True
    
    # Start capture in background thread
    threading.Thread(target=start_sniffing).start()
    
    return jsonify({
        'status': 'Capture started',
        'output_file': os.path.abspath(csv_file),
        'message': f"Capturing network traffic to {csv_file}"
    })

@prediction_routes.route('/stop_capture', methods=['POST'])
def stop_capture():
    global is_monitoring
    is_monitoring = False
    return jsonify({
        'status': 'Capture stopped',
        'output_file': os.path.abspath(csv_file),
        'message': f"Capture stopped. Data saved to {csv_file}"
    })