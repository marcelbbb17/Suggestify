from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow React to access this API

@app.route("/")
def home():
    return jsonify({"message": "Flask backend connected successfully!"})

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, port=5000)
