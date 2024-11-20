from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import json
import logging

host = "127.0.0.1"  # 소켓 서버 호스트
port = 5050  # 소켓 서버 포트

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 질문에 대한 응답을 받아오는 함수
def get_answer(query):
    try:
        mySocket = socket.socket()
        mySocket.connect((host, port))

        json_data = { # 요청할 질문 데이터
            'Query': query
            }
        message = json.dumps(json_data) # JSON 데이터로 변환
        mySocket.send(message.encode()) # 데이터 전송

        data = mySocket.recv(2048).decode()
        ret_data = json.loads(data) # 응답 데이터 파싱

        mySocket.close() # 소켓 연결 종료

        if 'response' not in ret_data: # 응답 데이터 검증
            raise ValueError("Invalid response format")

        return ret_data['response']
    except Exception as ex:
        raise Exception(f"Socket Error: {ex}")

# 사용자 질문 처리 POST API 엔드포인트
@app.route('/chatbot', methods=['POST'])
def query():
    app.logger.info("Received request")
    body = request.get_json()

    # 요청 데이터에 query 필드가 없을 경우 400 오류 반환
    if not body or 'query' not in body:
        return jsonify({'error': 'Bad Request', 'message': 'Query field is required'}), 400

    try:
        ret = get_answer(query=body['query'])
        return jsonify({'response': ret}), 200 # 응답 데이터 반환
    except Exception as ex:
        app.logger.error(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error', 'message': str(ex)}), 500

# 서버 상태 확인 GET API 엔드포인트
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'running'}), 200

if __name__ == '__main__':
    app.run(debug=True)