from flask import Blueprint, jsonify, session
import pandas as pd
from utils.benford_utils import apply_benford_law

feature_selection_routes = Blueprint('feature_selection_routes', __name__)

@feature_selection_routes.route('/feature_selection', methods=['POST'])
def feature_selection():
    dataset_path = session.get('dataset_path')
    if not dataset_path:
        return jsonify({"error": "No dataset uploaded"}), 400

    dataset = pd.read_csv(dataset_path)
    chi_results = apply_benford_law(dataset)

    if "error" in chi_results:
        return jsonify(chi_results), 400

    selected_features = chi_results["selected_features"]  # Store selected features
    session['selected_features'] = selected_features

    return jsonify({
        "message": "Feature Selection Done",
        "mean_threshold": chi_results["mean_threshold"],
        "median_threshold": chi_results["median_threshold"],
        "selected_features": selected_features,
        "results": chi_results["chi_stats"]
    })