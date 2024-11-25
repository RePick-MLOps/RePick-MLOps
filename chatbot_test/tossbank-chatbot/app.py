# pip install langchain chromadb transformers sentence-transformers pypdf langchain-community openai flask
from flask import Flask, request, jsonify
import models.chatbot

app = Flask(__name__)
bot = models.chatbot.toss_chatbot()

@app.route("/chat", methods=["POST"])
def inference():
    query = request.get_json()['query']
    return jsonify({'result': bot(query)['result']})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)