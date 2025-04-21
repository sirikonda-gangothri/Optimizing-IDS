let uploadedFiles = []; // Stores the uploaded files temporarily
let datasetType = ""; // Stores the dataset type (train, train_test, train_validation_test)
let loadingModal = null;

// Initialize loading modal
document.addEventListener('DOMContentLoaded', function() {
    loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    hideOutputSection(); // Hide output section initially
});

function showLoading(message = "Processing...") {
    document.getElementById('loadingMessage').textContent = message;
    loadingModal.show();
} 

function hideLoading() {
    loadingModal.hide();
}

function showOutputSection() {
    document.getElementById('outputSection').style.display = 'block';
}

function hideOutputSection() {
    document.getElementById('outputSection').style.display = 'none';
}

function clearCurrentStepOutput() {
    document.getElementById('currentStepOutput').innerHTML = '';
}

function updateStatusMessage(message, type = 'info') {
    const statusElement = document.getElementById('statusMessage');
    statusElement.className = `alert alert-${type}`;
    
    let icon = '';
    switch(type) {
        case 'info': icon = '<i class="fas fa-info-circle"></i> '; break;
        case 'success': icon = '<i class="fas fa-check-circle"></i> '; break;
        case 'warning': icon = '<i class="fas fa-exclamation-circle"></i> '; break;
        case 'danger': icon = '<i class="fas fa-times-circle"></i> '; break;
    }
    
    statusElement.innerHTML = icon + message;
}

// Function to load dataset based on type (train, train_test, or train_validation_test)
function loadDataset(type) {
    datasetType = type;
    let fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".csv";
    fileInput.multiple = (type === "train_test" || type === "train_validation_test");

    fileInput.addEventListener("change", function () {
        uploadedFiles = Array.from(this.files);
        if (uploadedFiles.length === 0) return;

        if (type === "train_validation_test" || type === "train_test") {
            // Show modal to specify file purposes
            showFilePurposeModal();
        } else {
            // Directly upload files for train option
            uploadFiles();
        }
    });

    fileInput.click();
}

// Function to show the file purpose modal
function showFilePurposeModal() {
    let filePurposeForm = document.getElementById("filePurposeForm");
    filePurposeForm.innerHTML = ""; // Clear previous content

    uploadedFiles.forEach((file, index) => {
        filePurposeForm.innerHTML += `
            <div class="mb-3">
                <label for="file${index + 1}" class="form-label" style="color: black;">File: ${file.name}</label>
                <select class="form-select" id="file${index + 1}Purpose">
                    ${datasetType === "train_test" ? `
                        <option value="train">Train</option>
                        <option value="test">Test</option>
                    ` : `
                        <option value="train">Train</option>
                        <option value="validation">Validation</option>
                        <option value="test">Test</option>
                    `}
                </select>
            </div>
        `;
    });

    // Show the modal
    let modal = new bootstrap.Modal(document.getElementById('filePurposeModal'));
    modal.show();
}

// Function to submit file purposes and upload files
function submitFilePurposes() {
    let filePurposes = [];
    uploadedFiles.forEach((file, index) => {
        let purpose = document.getElementById(`file${index + 1}Purpose`).value;
        filePurposes.push({ file, purpose });
    });

    // Upload files with their purposes
    uploadFiles(filePurposes);

    // Close the modal after submission
    let modal = bootstrap.Modal.getInstance(document.getElementById('filePurposeModal'));
    modal.hide();
}

// Function to upload files
function uploadFiles(filePurposes = []) {
    showLoading("Uploading dataset...");
    showOutputSection();
    clearCurrentStepOutput();
    
    let formData = new FormData();

    if (datasetType === "train_validation_test" || datasetType === "train_test") {
        filePurposes.forEach((item, index) => {
            formData.append(`file${index + 1}`, item.file);
            formData.append(`file${index + 1}_purpose`, item.purpose);
        });
    } else {
        uploadedFiles.forEach((file, index) => {
            formData.append(`file${index + 1}`, file);
        });
    }

    fetch(`/upload?type=${datasetType}`, {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.error) {
            updateStatusMessage(data.error, 'danger');
        } else {
            updateStatusMessage("Dataset uploaded successfully!", 'success');
            
            // Create the dimensions table rows
            const dimensionsRows = `
                <tr>
                    <td>Train Dataset</td>
                    <td>${data.train_dimensions || 'Not uploaded'}</td>
                </tr>
                <tr>
                    <td>Validation Dataset</td>
                    <td>${data.validation_dimensions || 'Not uploaded'}</td>
                </tr>
                <tr>
                    <td>Test Dataset</td>
                    <td>${data.test_dimensions || 'Not uploaded'}</td>
                </tr>
            `;

            const outputHTML = `
                <div class="step-result">
                    <h3 class="step-title">Dataset Upload Results</h3>
                    <div class="alert alert-success">
                        ${data.message}
                    </div>
                    <div class="mt-3">
                        <h4 style="color: lightblue;">Uploaded Files:</h4>
                        <ul>
                            ${data.details.map(file => `<li>${file}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="mt-3">
                        <h4 style="color: lightblue;">Dataset Dimensions:</h4>
                        <table class="data-table">
                            <tr>
                                <th>Dataset</th>
                                <th>Dimensions</th>
                            </tr>
                            ${dimensionsRows}
                        </table>
                    </div>
                </div>
            `;
            
            document.getElementById('currentStepOutput').innerHTML = outputHTML;
        }
    })
    .catch(error => {
        hideLoading();
        updateStatusMessage("Error uploading file(s): " + error.message, 'danger');
        console.error("Error:", error);
    });
}

// Function to process actions (Preprocessing)
// Function to process actions (Preprocessing)
function processData(action) {
    showLoading("Preprocessing data...");
    showOutputSection();
    clearCurrentStepOutput();
    
    fetch('/preprocess', {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        updateStatusMessage("Preprocessing completed successfully!", 'success');
        
        // Format preprocessing results
        const outputHTML = `
            <div class="step-result">
                <h3 class="step-title">Preprocessing Results</h3>
                <div class="alert alert-success">
                    ${data.message}
                </div>
                <div class="mt-3">
                    <h4 style="color: lightblue;">Dataset After Preprocessing:</h4>
                    <table class="data-table">
                        <tr>
                            <th>Dataset</th>
                            <th>Dimensions</th>
                        </tr>
                        <tr>
                            <td>Train Dataset</td>
                            <td>${data.train_dimensions || 'N/A'}</td>
                        </tr>
                        <tr>
                            <td>Validation Dataset</td>
                            <td>${data.validation_dimensions || 'N/A'}</td>
                        </tr>
                        <tr>
                            <td>Test Dataset</td>
                            <td>${data.test_dimensions || 'N/A'}</td>
                        </tr>
                    </table>
                </div>
                ${data.details ? `
                <div class="mt-3">
                    <h4 style="color: lightblue;">Details:</h4>
                    <ul>
                        ${data.details.map(detail => `<li>${detail}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        `;
        
        document.getElementById('currentStepOutput').innerHTML = outputHTML;
    })
    .catch(error => {
        hideLoading();
        updateStatusMessage("Preprocessing error: " + error.message, 'danger');
        console.error("Preprocessing Error:", error);
    });
}

// Function to perform feature selection
function featureSelection(method) {
    showLoading("Performing feature selection...");
    showOutputSection();
    clearCurrentStepOutput();
    
    fetch('/feature_selection', {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "method=" + encodeURIComponent(method)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.error) {
            updateStatusMessage(data.error, 'danger');
        } else {
            updateStatusMessage("Feature selection completed successfully!", 'success');
            
            // Format feature selection results
            const outputHTML = `
                <div class="step-result">
                    <h3 class="step-title">Feature Selection Results</h3>
                    <div class="alert alert-success">
                        Features selected using ${method} method
                    </div>
                    <div class="mt-3">
                        <h4 style="color: lightblue;">Thresholds:</h4>
                        <table class="data-table">
                            <tr>
                                <th>Mean Threshold</th>
                                <th>Median Threshold</th>
                            </tr>
                            <tr>
                                <td>${data.mean_threshold?.toFixed(2) || 'N/A'}</td>
                                <td>${data.median_threshold?.toFixed(2) || 'N/A'}</td>
                            </tr>
                        </table>
                    </div>
                    <div class="mt-3">
                        <h4 style="color: lightblue;">Selected Features (${data.selected_features?.length || 0}):</h4>
                        <div class="feature-list">
                            ${data.selected_features?.map(feature => 
                                `<div class="feature-item">${feature}</div>`
                            ).join('') || 'No features selected'}
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('currentStepOutput').innerHTML = outputHTML;
        }
    })
    .catch(error => {
        hideLoading();
        updateStatusMessage("Feature selection error: " + error.message, 'danger');
        console.error("Feature Selection Error:", error);
    });
}

// Function to normalize data
// Function to normalize data
function normalizeData(type) {
    showLoading(`Normalizing data (${type})...`);
    showOutputSection();
    clearCurrentStepOutput();
    
    fetch("/normalize", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "normalization_type=" + encodeURIComponent(type)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.error) {
            updateStatusMessage(data.error, 'danger');
        } else {
            updateStatusMessage(`Data normalized using ${type} method`, 'success');
            
            // Format normalization results
            const outputHTML = `
                <div class="step-result">
                    <h3 class="step-title">Normalization Results (${type})</h3>
                    <div class="alert alert-success">
                        ${data.message || "Data normalization completed"}
                    </div>
                    <div class="mt-3">
                        <h4 style="color: lightblue;">Normalized Dataset:</h4>
                        <table class="data-table">
                            <tr>
                                <th>Dataset</th>
                                <th>Dimensions</th>
                            </tr>
                            <tr>
                                <td>Train Dataset</td>
                                <td>${data.train_dimensions || 'N/A'}</td>
                            </tr>
                            <tr>
                                <td>Validation Dataset</td>
                                <td>${data.validation_dimensions || 'N/A'}</td>
                            </tr>
                            <tr>
                                <td>Test Dataset</td>
                                <td>${data.test_dimensions || 'N/A'}</td>
                            </tr>
                        </table>
                    </div>
                    ${data.columns ? `
                    <div class="mt-3">
                        <h4 style="color: lightblue;">Columns:</h4>
                        <div class="feature-list">
                            ${data.columns.map(col => `<div class="feature-item">${col}</div>`).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;
            
            document.getElementById('currentStepOutput').innerHTML = outputHTML;
        }
    })
    .catch(error => {
        hideLoading();
        updateStatusMessage("Normalization error: " + error.message, 'danger');
        console.error("Normalization Error:", error);
    });
}

// Function to train models
function trainModel(model) {
    const modelNames = {
        'decision_tree': 'Decision Tree',
        'naive_bayes': 'Naive Bayes',
        'knn': 'K-Nearest Neighbors',
        'svm': 'Support Vector Machine',
        'logistic_regression': 'Logistic Regression',
        'lda': 'Linear Discriminant Analysis',
        'qda': 'Quadratic Discriminant Analysis',
        'random_forest': 'Random Forest',
        'mlp': 'Multi-layer Perceptron',
        'gradient_boosting': 'Gradient Boosting'
    };

    // Validate model name
    if (!modelNames[model]) {
        updateStatusMessage(`Invalid model: ${model}`, 'danger');
        return;
    }

    showLoading(`Training ${modelNames[model]} model...`);
    showOutputSection();
    clearCurrentStepOutput();
    
    fetch(`/train?model=${model}`, { 
        method: "POST",
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(async response => {
        const contentType = response.headers.get('content-type');
        const responseData = contentType?.includes('application/json') 
            ? await response.json() 
            : { error: await response.text() };

        if (!response.ok) {
            throw new Error(responseData.error || `HTTP error! Status: ${response.status}`);
        }
        return responseData;
    })
    .then(data => {
        hideLoading();
        
        if (data.error) {
            throw new Error(data.error);
        }

        updateStatusMessage(`${modelNames[model]} model trained successfully`, 'success');
        
        const outputHTML = `
            <div class="step-result">
                <h3 class="step-title">${modelNames[model]} Results</h3>
                <div class="alert alert-success">
                    ${data.message}
                </div>
                <div class="mt-3">
                    <h4 style="color: lightblue;">Model Accuracy:</h4>
                    <table class="data-table">
                        <tr>
                            <th>Dataset</th>
                            <th>Accuracy</th>
                        </tr>
                        <tr>
                            <td>Validation</td>
                            <td>${(data.validation_accuracy * 100).toFixed(2)}%</td>
                        </tr>
                        <tr>
                            <td>Test</td>
                            <td>${(data.test_accuracy * 100).toFixed(2)}%</td>
                        </tr>
                    </table>
                </div>
                <div class="mt-3">
                    <p>Model saved as: <code>${data.model_path || model + '.pkl'}</code></p>
                </div>
                ${data.traceback ? `
                <div class="mt-3 alert alert-warning">
                    <h5>Debug Info:</h5>
                    <pre>${data.traceback}</pre>
                </div>
                ` : ''}
            </div>
        `;
        
        document.getElementById('currentStepOutput').innerHTML = outputHTML;
    })
    .catch(error => {
        hideLoading();
        let errorMsg = error.message;
        
        // Clean up HTML error messages
        if (errorMsg.includes('<') && errorMsg.includes('>')) {
            errorMsg = "Server returned an error page. Check console for details.";
        }
        
        updateStatusMessage(`Training error: ${errorMsg}`, 'danger');
        console.error("Full error:", error);
        
        document.getElementById('currentStepOutput').innerHTML = `
            <div class="alert alert-danger">
                <strong>Error training ${modelNames[model] || model}:</strong><br>
                ${errorMsg}<br><br>
                <button class="btn btn-sm btn-secondary" onclick="console.error('Full error:', ${JSON.stringify(error)})">
                    Show Error in Console
                </button>
            </div>
        `;
    });
}

