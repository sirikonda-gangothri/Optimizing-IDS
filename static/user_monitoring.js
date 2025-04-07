document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusElement = document.getElementById('status');
    const fileInfoElement = document.getElementById('fileInfo');
    const packetCountElement = document.getElementById('packetCount');
    const activityLog = document.getElementById('activityLog');
    const packetTableBody = document.getElementById('packetTableBody');
    
    // State variables
    let isCapturing = false;
    let packetDisplayInterval;
    let emptyRow = packetTableBody.querySelector('.empty-row');

    // Add log entry
    function addLogEntry(message) {
        const timestamp = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `[<span class="log-time">${timestamp}</span>] ${message}`;
        activityLog.appendChild(entry);
        activityLog.scrollTop = activityLog.scrollHeight;
    }

    // Update status
    function updateStatus(status, message) {
        statusElement.className = `status-card status-${status}`;
        statusElement.innerHTML = `
            <i class="fas fa-${getStatusIcon(status)}"></i>
            <span class="status-text">${message}</span>
        `;
        
        if (status === 'active') {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            isCapturing = true;
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            isCapturing = false;
        }
    }

    function getStatusIcon(status) {
        const icons = {
            ready: 'info-circle',
            active: 'play-circle',
            stopped: 'stop-circle',
            error: 'exclamation-circle'
        };
        return icons[status] || 'info-circle';
    }

    // Update packet display
    function updatePacketDisplay() {
        fetch('/get_packets')
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                // Remove empty row if it exists
                if (emptyRow) {
                    emptyRow.remove();
                    emptyRow = null;
                }

                packetTableBody.innerHTML = '';
                
                // Display packets in reverse chronological order
                data.packets.slice().reverse().forEach(packet => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${formatTime(packet.timestamp)}</td>
                        <td>${packet.source_ip}</td>
                        <td>${packet.destination_ip}</td>
                        <td>${packet.max_packet_length || 'N/A'}</td>
                        <td>${packet.init_win_bytes_forward || 'N/A'}</td>
                    `;
                    packetTableBody.appendChild(row);
                });

                // Update packet count
                packetCountElement.textContent = data.count || 0;
            })
            .catch(error => {
                console.error('Error fetching packets:', error);
            });
    }

    function formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }

    // Start capture
    startBtn.addEventListener('click', function() {
        fetch('/start_capture', { method: 'POST' })
            .then(response => {
                if (!response.ok) throw new Error('Failed to start capture');
                return response.json();
            })
            .then(data => {
                updateStatus('active', 'Capturing network traffic...');
                fileInfoElement.textContent = data.output_file;
                addLogEntry('Capture started');
                
                // Start updating packet display every 500ms
                packetDisplayInterval = setInterval(updatePacketDisplay, 500);
            })
            .catch(error => {
                updateStatus('error', 'Error starting capture');
                addLogEntry(`Error: ${error.message}`);
                console.error('Capture error:', error);
            });
    });

    // Stop capture
    stopBtn.addEventListener('click', function() {
        fetch('/stop_capture', { method: 'POST' })
            .then(response => {
                if (!response.ok) throw new Error('Failed to stop capture');
                return response.json();
            })
            .then(data => {
                clearInterval(packetDisplayInterval);
                updateStatus('stopped', 'Capture completed');
                addLogEntry(`Capture stopped. ${data.count} packets captured`);
                updatePacketDisplay(); // Final update
            })
            .catch(error => {
                updateStatus('error', 'Error stopping capture');
                addLogEntry(`Error: ${error.message}`);
            });
    });

    // Initial setup
    updateStatus('ready', 'Ready to start capture');
    addLogEntry('System initialized');
});