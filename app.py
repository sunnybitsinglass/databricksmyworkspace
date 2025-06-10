from flask import Flask, send_from_directory, request, jsonify, current_app
#from flask_cors import CORS
import os
import requests
import logging
from dotenv import load_dotenv

# Load .env support
load_dotenv()

# --- Logging Setup ---
# Configure basic logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Flask App Setup ---
app = Flask(__name__, static_folder='frontend')
#CORS(app, origins="http://localhost:3000", supports_credentials=True)
@app.route('/')
def serve_index():
    logger.info(f"Serving index.html from: {app.static_folder}")
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_any_path(path):
    file_path = os.path.join(app.static_folder, path)
    logger.info(f"Attempting to serve: {file_path}")
    if os.path.exists(file_path):
        logger.info(f"Serving static file: {file_path}")
        return send_from_directory(app.static_folder, path)
    else:
        logger.info(f"Serving index.html for unknown path: {path}")
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/get-chat-bot-data', methods=['POST'])
def get_chat_bot_data():
    try:
        # App config for Databricks
        app.config["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN")
        app.config["DATABRICKS_URL"] = os.getenv("DATABRICKS_URL")
        prompt = request.json.get('prompt')
        if not prompt:
            logger.warning("Received request with no prompt.")
            return jsonify({"error": "Prompt is required"}), 400

        headers = {
            'Authorization': f'Bearer {app.config["DATABRICKS_TOKEN"]}',
            'Content-Type': 'application/json'
        }

        payload = {
            'inputs': {
                'query': prompt
            }
        }

        logger.info(f"Sending request to Databricks with prompt: {prompt}")
        response = requests.post(app.config["DATABRICKS_URL"], json=payload, headers=headers, verify=True)
        response.raise_for_status()
        data = response.json()

        logger.info(f"Databricks API Response: {data}")
        if not data:
            logger.warning("Databricks API returned no data.")
            return jsonify({"error": "No data found"}), 404
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error posting query to Databricks: {e}")
        return jsonify({"error": "Sorry something went wrong."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return jsonify({"error": "Sorry something went wrong."}), 500

# Do not use app.run() in Databricks
if __name__ == '__main__':
    logger.info("Starting Flask application in development mode.")
    app.run(debug=True, port=8000)
