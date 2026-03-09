from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Configuration
app.config['DATASET_PATH'] = os.environ.get('DATASET_PATH', './dataset')
app.config['DATABASE_PATH'] = os.path.join('app', 'data', 'dataset_analysis.db')
app.config['THUMBNAIL_SIZE'] = (150, 150)

@app.route('/api/health')
def health_check():
    """Health check endpoint to verify server status"""
    import sys
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'flask_version': Flask.__version__
    })

@app.route('/')
def index():
    """Serve the main HTML page"""
    return "Image Detection Result Analyzer - Backend Running"

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)
    os.makedirs(os.path.join('app', 'static', 'thumbnails'), exist_ok=True)

    print("==========================================")
    print("Image Detection Result Analyzer")
    print("Flask Server Starting...")
    print("==========================================")
    print(f"Python Version: {app.config['python_version']}")
    print(f"Flask Version: {Flask.__version__}")
    print(f"Dataset Path: {app.config['DATASET_PATH']}")
    print(f"Database Path: {app.config['DATABASE_PATH']}")
    print("==========================================")

    app.run(debug=True, host='0.0.0.0', port=5000)
