from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = 'secret'
app.config['SECRET_KEY'] = 'secret'

CORS(app)  # Enable CORS

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=20356, debug=True)
