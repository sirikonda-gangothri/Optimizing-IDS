from flask import Blueprint, jsonify, request
import pandas as pd
import os
import joblib
import traceback
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

train_model_routes = Blueprint('train_model_routes', __name__)

def get_classifier(model_name):
    classifiers = {
        'decision_tree': DecisionTreeClassifier(criterion='gini', random_state=42, max_depth=5),
        'naive_bayes': GaussianNB(),
        'knn': KNeighborsClassifier(n_neighbors=5),
        'svm': SVC(kernel='rbf', random_state=42, probability=True),
        'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
        'lda': LinearDiscriminantAnalysis(),
        'qda': QuadraticDiscriminantAnalysis(),
        'random_forest': RandomForestClassifier(random_state=42, n_estimators=100),
        'mlp': MLPClassifier(random_state=42, hidden_layer_sizes=(100,), max_iter=1000),
        'gradient_boosting': GradientBoostingClassifier(random_state=42)
    }
    return classifiers.get(model_name.lower())

@train_model_routes.route('/train', methods=['POST'])
def train():
    try:
        model_name = request.args.get('model', 'decision_tree')
        
        # Validate model name
        valid_models = ['decision_tree', 'naive_bayes', 'knn', 'svm', 
                       'logistic_regression', 'lda', 'qda', 
                       'random_forest', 'mlp', 'gradient_boosting']
        if model_name not in valid_models:
            return jsonify({
                "error": f"Invalid model specified. Available models: {', '.join(valid_models)}"
            }), 400

        # Check if required files exist
        required_files = ['train.csv', 'validation.csv', 'test.csv']
        missing_files = [f for f in required_files if not os.path.exists(os.path.join('uploads', f))]
        if missing_files:
            return jsonify({
                "error": f"Missing required files: {', '.join(missing_files)}",
                "available_files": os.listdir('uploads')
            }), 400

        # Load datasets
        train_df = pd.read_csv(os.path.join('uploads', "train.csv"))
        val_df = pd.read_csv(os.path.join('uploads', "validation.csv"))
        test_df = pd.read_csv(os.path.join('uploads', "test.csv"))

        # Validate columns
        if not (train_df.shape[1] == val_df.shape[1] == test_df.shape[1]):
            return jsonify({
                "error": "All datasets must have the same number of features/columns",
                "details": {
                    "train_columns": train_df.shape[1],
                    "validation_columns": val_df.shape[1],
                    "test_columns": test_df.shape[1]
                }
            }), 400

        # Prepare data
        X_train = train_df.iloc[:, :-1].values
        y_train = train_df.iloc[:, -1].values
        X_val = val_df.iloc[:, :-1].values
        y_val = val_df.iloc[:, -1].values
        X_test = test_df.iloc[:, :-1].values
        y_test = test_df.iloc[:, -1].values

        # Get and train classifier
        classifier = get_classifier(model_name)
        classifier.fit(X_train, y_train)

        # Calculate metrics
        val_accuracy = accuracy_score(y_val, classifier.predict(X_val))
        test_accuracy = accuracy_score(y_test, classifier.predict(X_test))

        # Save model
        os.makedirs('models', exist_ok=True)
        model_path = os.path.join('models', f"{model_name}.pkl")
        joblib.dump(classifier, model_path)

        return jsonify({
            "message": f"{model_name.replace('_', ' ').title()} model trained successfully",
            "model": model_name,
            "validation_accuracy": round(val_accuracy, 4),
            "test_accuracy": round(test_accuracy, 4),
            "model_path": model_path
        })

    except Exception as e:
        return jsonify({
            "error": f"Error training {model_name} model: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500