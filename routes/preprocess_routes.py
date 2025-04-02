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

    for dataset_name in datasets:
        dataset_path = os.path.join('uploads', f"{dataset_name}.csv")
        if not os.path.exists(dataset_path):
            logging.warning(f"{dataset_name.capitalize()} dataset not found at {dataset_path}")
            results.append(f"{dataset_name.capitalize()} dataset not found.")
            continue

        try:
            # Load the dataset
            dataset = pd.read_csv(dataset_path)
            
            # Replace missing values
            dataset.dropna(inplace=True)
            
            # Apply correlation-based feature elimination
            dataset, removed_features = CORRELATED(dataset)
            
            # Save the preprocessed dataset
            dataset.to_csv(dataset_path, index=False)
            results.append(f"{dataset_name.capitalize()} Dataset Preprocessed: {dataset.shape[0]} rows, {dataset.shape[1]} columns.")
            logging.info(f"{dataset_name.capitalize()} dataset preprocessed successfully.")
        except Exception as e:
            logging.error(f"Error preprocessing {dataset_name.capitalize()} dataset: {e}")
            results.append(f"{dataset_name.capitalize()} Dataset Preprocessing Failed: {str(e)}")

    return jsonify({
        "message": "Preprocessing completed successfully!",
        "results": results
    })