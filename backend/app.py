from flask import Flask, jsonify
from flask_cors import CORS
from routes import register_blueprints
from config import get_config
import os

def create_app():
    app = Flask(__name__)
    CORS(app) 
    
    config = get_config()
    
    register_blueprints(app)
    
    @app.route("/")
    def home():
        return jsonify({"welcome": "Welcome to the Suggestify API!"})
    
    return app

if __name__ == "__main__":
    print("Starting Flask server...")
    app = create_app()

    port = int(os.environ.get('PORT', 5000))

    if os.environ.get('RENDER'):
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        app.run(debug=True, port=5000)