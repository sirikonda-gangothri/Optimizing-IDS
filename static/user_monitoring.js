document.addEventListener('DOMContentLoaded', function() {
    // Get all required elements
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusElement = document.getElementById('status');
    const fileInfoElement = document.getElementById('fileInfo');
    const packetCountElement = document.getElementById('packetCount');
    const activityLog = document.getElementById('activityLog');
    
    let isCapturing = false;
    let packetCount = 0;
    let updateInterval;

    // Add log entry function
    function addLogEntry(message) {
        const timestamp = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.textContent = `[${timestamp}] ${message}`;
        activityLog.appendChild(entry);
        activityLog.scrollTop = activityLog.scrollHeight;
    }

    // Update status function
    function updateStatus(status, message) {
        statusElement.className = `status status-${status}`;
        
        const icons = {
            ready: 'info-circle',
            active: 'play-circle',
            stopped: 'stop-circle',
            error: 'exclamation-circle'
        };
        
        statusElement.innerHTML = `<i class="fas fa-${icons[status]}"></i> ${message}`;
        
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

    // Update packet count (simulated)
    function updatePacketCounter() {
        if (isCapturing) {
            packetCount++;
            packetCountElement.textContent = packetCount;
        }
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
                
                // Start updating packet count (simulated)
                updateInterval = setInterval(updatePacketCounter, 300);
            })
            .catch(error => {
                updateStatus('error', error.message);
                addLogEntry(`Error: ${error.message}`);
            });
    });

    // Stop capture
    stopBtn.addEventListener('click', function() {
        fetch('/stop_capture', { method: 'POST' })
            .then(response => {
                if (!response.ok) throw new Error('Failed to stop capture');
                clearInterval(updateInterval);
                updateStatus('stopped', 'Capture completed');
                addLogEntry(`Capture stopped. ${packetCount} packets captured`);
            })
            .catch(error => {
                updateStatus('error', error.message);
                addLogEntry(`Error: ${error.message}`);
            });
    });

    // Initial setup
    updateStatus('ready', 'Ready to start capture');
    addLogEntry('System initialized');
});