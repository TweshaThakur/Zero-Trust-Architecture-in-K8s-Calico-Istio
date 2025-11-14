from flask import Flask, jsonify
from datetime import datetime
import socket

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'healthy',
        'service': 'backend',
        'hostname': socket.gethostname(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/data')
def get_data():
    return jsonify({
        'message': 'Hello from Backend!',
        'data': {
            'items': ['Item 1', 'Item 2', 'Item 3'],
            'count': 3
        },
        'hostname': socket.gethostname(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
