from flask import Blueprint, request, jsonify, session
import os
import pandas as pd
from sklearn.model_selection import train_test_split

upload_routes = Blueprint('upload_routes', __name__)

UPLOAD_FOLDER = 'uploads'

@upload_routes.route('/upload', methods=['POST'])
def upload_file():
    dataset_type = request.args.get('type', 'train')  # Type of dataset being uploaded
    files = [request.files.get(f'file{i + 1}') for i in range(len(request.files))]
    purposes = [request.form.get(f'file{i + 1}_purpose') for i in range(len(request.files))]
    details = []
    dimensions = {
        'train_dimensions': 'Not uploaded',
        'validation_dimensions': 'Not uploaded',
        'test_dimensions': 'Not uploaded'
    }

    # Ensure the correct number of files are uploaded based on the dataset type
    if dataset_type == "train" and len(files) != 1:
        return jsonify({"error": "Please upload exactly 1 file for the Train dataset."}), 400
    elif dataset_type == "train_test" and len(files) != 2:
        return jsonify({"error": "Please upload exactly 2 files for Train + Test datasets."}), 400
    elif dataset_type == "train_validation_test" and len(files) != 3:
        return jsonify({"error": "Please upload exactly 3 files for Train + Validation + Test datasets."}), 400

    # Save files and assign them to their respective purposes
    for i, file in enumerate(files):
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        dataset = pd.read_csv(file_path)

        if 'Label' not in dataset.columns:
            return jsonify({"error": "Dataset must have a 'Label' column"}), 400

        # Assign file to its purpose
        if dataset_type == "train_validation_test" or dataset_type == "train_test":
            purpose = purposes[i]
            dataset.to_csv(os.path.join(UPLOAD_FOLDER, f"{purpose}.csv"), index=False)
            details.append(f"{file.filename} uploaded as {purpose} dataset: {dataset.shape[0]} rows, {dataset.shape[1]} columns")
        else:
            details.append(f"{file.filename}: {dataset.shape[0]} rows, {dataset.shape[1]} columns")

    # Process datasets based on the type
    if dataset_type == "train":
        # Split the single file into train, validation, and test datasets
        train_df, val_test_df = train_test_split(dataset, test_size=0.3, random_state=42)
        val_df, test_df = train_test_split(val_test_df, test_size=0.5, random_state=42)

        train_path = os.path.join(UPLOAD_FOLDER, "train.csv")
        val_path = os.path.join(UPLOAD_FOLDER, "validation.csv")
        test_path = os.path.join(UPLOAD_FOLDER, "test.csv")
        
        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)

        dimensions = {
            'train_dimensions': f"{train_df.shape[0]} rows, {train_df.shape[1]} columns",
            'validation_dimensions': f"{val_df.shape[0]} rows, {val_df.shape[1]} columns",
            'test_dimensions': f"{test_df.shape[0]} rows, {test_df.shape[1]} columns"
        }
        details.append("Train dataset split into Train, Validation, and Test sets.")

    elif dataset_type == "train_test":
        # [Previous train_test processing code...]
        dimensions = {
            'train_dimensions': f"{train_df.shape[0]} rows, {train_df.shape[1]} columns",
            'test_dimensions': f"{test_df.shape[0]} rows, {test_df.shape[1]} columns"
        }
        details.append("Train and Test datasets uploaded successfully.")

    elif dataset_type == "train_validation_test":
        # For this case, dimensions are already set from the file saving loop
        dimensions = {}
        for purpose in purposes:
            if purpose == 'train':
                dimensions['train_dimensions'] = f"{pd.read_csv(os.path.join(UPLOAD_FOLDER, 'train.csv')).shape[0]} rows, {pd.read_csv(os.path.join(UPLOAD_FOLDER, 'train.csv')).shape[1]} columns"
            elif purpose == 'validation':
                dimensions['validation_dimensions'] = f"{pd.read_csv(os.path.join(UPLOAD_FOLDER, 'validation.csv')).shape[0]} rows, {pd.read_csv(os.path.join(UPLOAD_FOLDER, 'validation.csv')).shape[1]} columns"
            elif purpose == 'test':
                dimensions['test_dimensions'] = f"{pd.read_csv(os.path.join(UPLOAD_FOLDER, 'test.csv')).shape[0]} rows, {pd.read_csv(os.path.join(UPLOAD_FOLDER, 'test.csv')).shape[1]} columns"

    # Update session
    session['dataset_path'] = os.path.join(UPLOAD_FOLDER, "train.csv")
    session['dataset_type'] = dataset_type

    return jsonify({
        "message": "Dataset(s) uploaded and processed successfully!",
        "details": details,
        **dimensions
    })

@upload_routes.route('/get_dataset_dimensions', methods=['GET'])
def get_dataset_dimensions():
    datasets = ["train", "validation", "test"]
    dimensions = {}

    for dataset_name in datasets:
        dataset_path = os.path.join(UPLOAD_FOLDER, f"{dataset_name}.csv")
        if os.path.exists(dataset_path):
            dataset = pd.read_csv(dataset_path)
            dimensions[f"{dataset_name}_dimensions"] = f"{dataset.shape[0]} rows, {dataset.shape[1]} columns"
        else:
            dimensions[f"{dataset_name}_dimensions"] = "Not uploaded"

    return jsonify(dimensions)