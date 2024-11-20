from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import json
import logging

host = "127.0.0.1"
port = 5050

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_answer(query):
    try:
        mySocket = socket.socket()
        mySocket.connect((host, port))

        json_data = {'Query': query}
        message = json.dumps(json_data)
        mySocket.send(message.encode())

        data = mySocket.recv(2048).decode()
        ret_data = json.loads(data)

        mySocket.close()

        if 'response' not in ret_data:
            raise ValueError("Invalid response format")

        return ret_data['response']
    except Exception as ex:
        raise Exception(f"Socket Error: {ex}")

@app.route('/chatbot', methods=['POST'])
def query():
    app.logger.info("Received request")
    body = request.get_json()

    if not body or 'query' not in body:
        return jsonify({'error': 'Bad Request', 'message': 'Query field is required'}), 400

    try:
        ret = get_answer(query=body['query'])
        return jsonify({'response': ret}), 200
    except Exception as ex:
        app.logger.error(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error', 'message': str(ex)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'running'}), 200

if __name__ == '__main__':
    app.run(debug=True)