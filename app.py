from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# Set OpenAI API key from environment variable (recommended) or hardcoded
openai.api_key = os.environ.get('OPENAI_API_KEY', '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')

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'success',
        'message': 'OpenAI Backend API is running'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        messages = data.get('messages', [])
        model = data.get('model', 'gpt-3.5-turbo')
        
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        # Make request to OpenAI
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages
        )
        
        return jsonify({
            'status': 'success',
            'response': response.choices[0].message.content,
            'usage': response.usage
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/completion', methods=['POST'])
def completion():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        model = data.get('model', 'gpt-3.5-turbo-instruct')
        max_tokens = data.get('max_tokens', 100)
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Make request to OpenAI
        response = openai.Completion.create(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens
        )
        
        return jsonify({
            'status': 'success',
            'response': response.choices[0].text,
            'usage': response.usage
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
