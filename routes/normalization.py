from flask import Blueprint, request, jsonify, session
import pandas as pd
import os
from sklearn.preprocessing import MinMaxScaler, StandardScaler, QuantileTransformer

normalization_routes = Blueprint('normalization_routes', __name__)

@normalization_routes.route('/normalize', methods=['POST'])
def normalize():
    normalization_type = request.form.get('normalization_type', 'minmax')
    datasets = ["train", "validation", "test"]
    results = []
    dimensions = {}

    for dataset_name in datasets:
        dataset_path = os.path.join('uploads', f"{dataset_name}.csv")
        if not os.path.exists(dataset_path):
            dimensions[f"{dataset_name}_dimensions"] = "N/A"
            continue

        try:
            dataset = pd.read_csv(dataset_path)
            
            # Get features (excluding Label)
            features = [col for col in dataset.columns if col != 'Label']
            
            if normalization_type == "minmax":
                scaler = MinMaxScaler()
            elif normalization_type == "standard":
                scaler = StandardScaler()
            elif normalization_type == "quantile":
                scaler = QuantileTransformer(output_distribution='normal')
            else:
                return jsonify({"error": "Invalid normalization type"}), 400

            # Normalize features
            dataset[features] = scaler.fit_transform(dataset[features])
            
            # Save normalized dataset
            normalized_path = os.path.join('uploads', f"{dataset_name}_normalized.csv")
            dataset.to_csv(normalized_path, index=False)
            
            dimensions[f"{dataset_name}_dimensions"] = f"{dataset.shape[0]} rows, {dataset.shape[1]} columns"
            
        except Exception as e:
            dimensions[f"{dataset_name}_dimensions"] = "N/A"
            continue

    return jsonify({
        "message": f"Normalization completed successfully using {normalization_type} method",
        **dimensions,
        "columns": features
    })