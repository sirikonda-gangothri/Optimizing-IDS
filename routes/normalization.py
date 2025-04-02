from flask import Blueprint, request, jsonify, session
import pandas as pd
import os
from sklearn.preprocessing import MinMaxScaler, StandardScaler, QuantileTransformer

normalization_routes = Blueprint('normalization_routes', __name__)

@normalization_routes.route('/normalize', methods=['POST'])
def normalize():
    dataset_path = session.get('dataset_path')
    selected_features = session.get('selected_features')

    if not dataset_path or not selected_features:
        return jsonify({"error": "Feature selection not done"}), 400

    dataset = pd.read_csv(dataset_path)
    normalization_type = request.form.get('normalization_type', 'minmax')

    feature_data = dataset[selected_features].drop(columns=['Label'], errors='ignore')

    if normalization_type == "minmax":
        scaler = MinMaxScaler()
    elif normalization_type == "standard":
        scaler = StandardScaler()
    elif normalization_type == "quantile":
        scaler = QuantileTransformer(output_distribution='normal')
    else:
        return jsonify({"error": "Invalid normalization type"}), 400

    normalized_data = pd.DataFrame(scaler.fit_transform(feature_data), columns=feature_data.columns)
    normalized_data['Label'] = dataset['Label'].values

    normalized_path = os.path.join('uploads', "normalized.csv")
    normalized_data.to_csv(normalized_path, index=False)

    return jsonify({
        "message": "Normalization completed successfully!",
        "normalized_file": "normalized.csv",
        "columns": normalized_data.columns.tolist(),
        "shape": normalized_data.shape
    })