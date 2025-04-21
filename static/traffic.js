document.addEventListener('DOMContentLoaded', function() {
    // Model handling
    const modelUpload = document.getElementById('modelUpload');
    const modelStatus = document.getElementById('modelStatus');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusElement = document.getElementById('status');
    const fileInfoElement = document.getElementById('fileInfo');
    const packetCountElement = document.getElementById('packetCount');
    const threatLevelElement = document.getElementById('threatLevel');
    const trafficGraph = document.getElementById('trafficGraph');
    const predictionTableBody = document.getElementById('predictionTableBody');
    const activityLog = document.getElementById('activityLog');
    
    let modelLoaded = false;
    let isMonitoring = false;
    let updateInterval;
    
    // Model upload handler
    modelUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('model', file);
        
        fetch('/load_model', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                modelStatus.textContent = 'Error loading model';
                modelStatus.className = 'text-danger';
                statusElement.className = 'status-card status-error';
                statusElement.querySelector('.status-text').textContent = 'Model load failed';
                addLogEntry(`Failed to load model: ${data.error}`, 'error');
                return;
            }
            
            modelLoaded = true;
            modelStatus.textContent = file.name;
            modelStatus.className = 'text-success';
            startBtn.disabled = false;
            statusElement.className = 'status-card status-ready';
            statusElement.querySelector('.status-text').textContent = 'Ready to start analysis';
            
            // Update UI with model info
            addLogEntry(`Model loaded: ${data.model_type}`, 'success');
            addLogEntry(`Features: ${data.features.length || 'Unknown'}`, 'info');
            addLogEntry(`Classes: ${data.classes.join(', ')}`, 'info');
        })
        .catch(error => {
            modelStatus.textContent = 'Error loading model';
            modelStatus.className = 'text-danger';
            addLogEntry(`Error loading model: ${error.message}`, 'error');
        });
    });
    
    // Start capture handler
    startBtn.addEventListener('click', function() {
        if (!modelLoaded) return;
        
        fetch('/start_capture', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addLogEntry(`Error starting capture: ${data.error}`, 'error');
                return;
            }
            
            isMonitoring = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusElement.className = 'status-card status-active';
            statusElement.querySelector('.status-text').textContent = 'Monitoring network traffic';
            fileInfoElement.textContent = data.output_file;
            
            // Start updating UI
            updateInterval = setInterval(updateUI, 1000);
            addLogEntry('Started network traffic capture', 'success');
        })
        .catch(error => {
            addLogEntry(`Error starting capture: ${error.message}`, 'error');
        });
    });
    
    // Stop capture handler
    stopBtn.addEventListener('click', function() {
        fetch('/stop_capture', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            isMonitoring = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusElement.className = 'status-card status-ready';
            statusElement.querySelector('.status-text').textContent = 'Capture stopped';
            
            clearInterval(updateInterval);
            addLogEntry(`Stopped capture. ${data.count} packets analyzed`, 'info');
        })
        .catch(error => {
            addLogEntry(`Error stopping capture: ${error.message}`, 'error');
        });
    });
    
    // Update UI with latest data
    function updateUI() {
        fetch('/get_predictions')
        .then(response => response.json())
        .then(data => {
            // Update packet count
            packetCountElement.textContent = data.count;
            
            // Update threat level based on recent predictions
            updateThreatLevel(data.predictions);
            
            // Update graph
            if (data.graph) {
                trafficGraph.src = `data:image/png;base64,${data.graph}`;
                trafficGraph.style.display = 'block';
            }
            
            // Update prediction table
            updatePredictionTable(data.predictions);
        })
        .catch(error => {
            console.error('Error updating UI:', error);
        });
    }
    
    // Update threat level indicator
    function updateThreatLevel(predictions) {
        if (predictions.length === 0) {
            threatLevelElement.textContent = 'Unknown';
            threatLevelElement.className = 'stat-value';
            return;
        }
        
        // Count malicious predictions
        const maliciousCount = predictions.filter(p => 
            p.prediction && (p.prediction.includes('DDoS') || p.prediction.includes('Malicious'))
        ).length;
        
        const threatPercentage = (maliciousCount / predictions.length) * 100;
        
        if (threatPercentage > 30) {
            threatLevelElement.textContent = 'High';
            threatLevelElement.className = 'stat-value text-danger';
        } else if (threatPercentage > 10) {
            threatLevelElement.textContent = 'Medium';
            threatLevelElement.className = 'stat-value text-warning';
        } else if (maliciousCount > 0) {
            threatLevelElement.textContent = 'Low';
            threatLevelElement.className = 'stat-value text-info';
        } else {
            threatLevelElement.textContent = 'None';
            threatLevelElement.className = 'stat-value text-success';
        }
    }
    
    // Update prediction table
    function updatePredictionTable(predictions) {
        // Clear existing rows
        while (predictionTableBody.firstChild) {
            predictionTableBody.removeChild(predictionTableBody.firstChild);
        }
        
        if (predictions.length === 0) {
            const row = document.createElement('tr');
            row.className = 'empty-row';
            row.innerHTML = '<td colspan="5">No predictions yet</td>';
            predictionTableBody.appendChild(row);
            return;
        }
        
        // Show last 10 predictions
        const recentPredictions = predictions.slice(-10).reverse();
        
        recentPredictions.forEach(pred => {
            const row = document.createElement('tr');
            
            // Determine row class based on prediction
            if (pred.prediction && (pred.prediction.includes('DDoS') || pred.prediction.includes('Malicious'))) {
                row.className = 'table-danger';
            } else {
                row.className = 'table-success';
            }
            
            // Format timestamp
            const timestamp = new Date(pred.timestamp);
            const formattedTime = timestamp.toLocaleTimeString();
            
            // Format confidence
            const confidence = pred.confidence ? (pred.confidence * 100).toFixed(1) + '%' : 'N/A';
            
            row.innerHTML = `
                <td>${formattedTime}</td>
                <td>${pred.source_ip || 'N/A'}</td>
                <td>${pred.destination_ip || 'N/A'}</td>
                <td>${pred.packet_length || 'N/A'}</td>
                <td>
                    ${pred.prediction || 'N/A'}
                    ${confidence ? `<br><small class="text-muted">${confidence}</small>` : ''}
                </td>
            `;
            
            predictionTableBody.appendChild(row);
        });
    }
    
    // Add entry to activity log
    function addLogEntry(message, type = 'info') {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        
        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;
        entry.innerHTML = `[<span class="log-time">${timeString}</span>] ${message}`;
        
        activityLog.insertBefore(entry, activityLog.firstChild);
        
        // Keep log to reasonable size
        if (activityLog.children.length > 50) {
            activityLog.removeChild(activityLog.lastChild);
        }
    }
    
    // Initialize UI
    function initUI() {
        startBtn.disabled = true;
        stopBtn.disabled = true;
        trafficGraph.style.display = 'none';
        addLogEntry('System initialized', 'info');
    }
    
    initUI();
});