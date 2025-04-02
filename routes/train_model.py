from flask import Blueprint, jsonify
import pandas as pd
import os
import joblib
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import accuracy_score

train_model_routes = Blueprint('train_model_routes', __name__)

@train_model_routes.route('/train', methods=['POST'])
def train():
    # Load datasets
    train_df = pd.read_csv(os.path.join('uploads', "train.csv"))
    val_df = pd.read_csv(os.path.join('uploads', "validation.csv"))
    test_df = pd.read_csv(os.path.join('uploads', "test.csv"))

    # Debug: Print columns in each dataset
    print(f"Training dataset columns: {train_df.columns.tolist()}")
    print(f"Validation dataset columns: {val_df.columns.tolist()}")
    print(f"Test dataset columns: {test_df.columns.tolist()}")

    # Ensure all datasets have the same columns
    train_columns = train_df.columns.tolist()
    val_columns = val_df.columns.tolist()
    test_columns = test_df.columns.tolist()

    # Find missing columns in validation and test datasets
    missing_in_val = set(train_columns) - set(val_columns)
    missing_in_test = set(train_columns) - set(test_columns)

    # Add missing columns to validation and test datasets (with default values)
    for column in missing_in_val:
        val_df[column] = 0  # Fill missing columns with 0 or another appropriate default value

    for column in missing_in_test:
        test_df[column] = 0  # Fill missing columns with 0 or another appropriate default value

    # Reorder columns in validation and test datasets to match the training dataset
    val_df = val_df[train_columns]
    test_df = test_df[train_columns]

    # Debug: Print shapes of datasets
    print(f"Training dataset shape: {train_df.shape}")
    print(f"Validation dataset shape: {val_df.shape}")
    print(f"Test dataset shape: {test_df.shape}")

    # Prepare features and labels
    X_train = train_df.iloc[:, :-1].values
    y_train = train_df.iloc[:, -1].values

    X_val = val_df.iloc[:, :-1].values
    y_val = val_df.iloc[:, -1].values

    X_test = test_df.iloc[:, :-1].values
    y_test = test_df.iloc[:, -1].values

    # Train the model
    dt_classifier = DecisionTreeClassifier()
    dt_classifier.fit(X_train, y_train)

    # Validate model
    val_predictions = dt_classifier.predict(X_val)
    val_accuracy = accuracy_score(y_val, val_predictions)

    # Test model
    test_predictions = dt_classifier.predict(X_test)
    test_accuracy = accuracy_score(y_test, test_predictions)

    # Save the model
    model_path = os.path.join('models', "decision_tree.pkl")
    joblib.dump(dt_classifier, model_path)

    # Export decision tree rules
    tree_rules = export_text(dt_classifier, feature_names=train_df.columns[:-1].tolist())
    return jsonify({
        "message": "Model Trained",
        "tree_structure": tree_rules,
        "validation_accuracy": val_accuracy,
        "test_accuracy": test_accuracy
    })