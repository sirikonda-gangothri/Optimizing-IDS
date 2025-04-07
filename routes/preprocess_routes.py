from flask import Blueprint, jsonify
import pandas as pd
import os
import logging
from utils.correlated_utils import CORRELATED

preprocess_routes = Blueprint('preprocess_routes', __name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
    
@preprocess_routes.route('/preprocess', methods=['POST'])
def preprocess():
    datasets = ["train", "validation", "test"]
    results = []
    dimensions = {}

    for dataset_name in datasets:
        dataset_path = os.path.join('uploads', f"{dataset_name}.csv")
        if not os.path.exists(dataset_path):
            logging.warning(f"{dataset_name.capitalize()} dataset not found at {dataset_path}")
            results.append(f"{dataset_name.capitalize()} dataset not found.")
            dimensions[f"{dataset_name}_dimensions"] = "N/A"
            dimensions[f"{dataset_name}_missing"] = "N/A"
            continue

        try:
            # Load the dataset
            dataset = pd.read_csv(dataset_path)
            
            # Store original dimensions
            original_rows, original_cols = dataset.shape
            
            # Replace missing values
            missing_before = dataset.isnull().sum().sum()
            dataset.dropna(inplace=True)
            missing_after = dataset.isnull().sum().sum()
            
            # Apply correlation-based feature elimination
            dataset, removed_features = CORRELATED(dataset)
            
            # Save the preprocessed dataset
            dataset.to_csv(dataset_path, index=False)
            
            # Store results
            results.append(f"{dataset_name.capitalize()} Dataset Preprocessed: {dataset.shape[0]} rows, {dataset.shape[1]} columns.")
            dimensions[f"{dataset_name}_dimensions"] = f"{dataset.shape[0]} rows, {dataset.shape[1]} columns"
            dimensions[f"{dataset_name}_missing"] = f"{missing_before} → {missing_after}"
            
            logging.info(f"{dataset_name.capitalize()} dataset preprocessed successfully.")
        except Exception as e:
            logging.error(f"Error preprocessing {dataset_name.capitalize()} dataset: {e}")
            results.append(f"{dataset_name.capitalize()} Dataset Preprocessing Failed: {str(e)}")
            dimensions[f"{dataset_name}_dimensions"] = "N/A"
            dimensions[f"{dataset_name}_missing"] = "N/A"

    return jsonify({
        "message": "Preprocessing completed successfully!",
        "details": results,
        **dimensions
    })
