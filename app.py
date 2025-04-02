from flask import Flask, render_template  # Added render_template import
from routes.auth_routes import auth_routes
from routes.upload_routes import upload_routes
from routes.preprocess_routes import preprocess_routes
from routes.feature_selection import feature_selection_routes
from routes.normalization import normalization_routes
from routes.train_model import train_model_routes
from routes.prediction_routes import prediction_routes
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Create necessary folders
UPLOAD_FOLDER = 'uploads'
MODEL_FOLDER = 'models'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)

# Register blueprints
app.register_blueprint(auth_routes)
app.register_blueprint(upload_routes)
app.register_blueprint(preprocess_routes)
app.register_blueprint(feature_selection_routes)
app.register_blueprint(normalization_routes)
app.register_blueprint(train_model_routes)
app.register_blueprint(prediction_routes)

# Route for user monitoring (must come before the __main__ check)
@app.route('/user_monitoring')
def user_monitoring():
    return render_template('user_monitoring.html')

if __name__ == '__main__':
    app.run(debug=True)