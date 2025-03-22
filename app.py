from flask import Flask, render_template, jsonify
import main as be

app = Flask(__name__)

@app.route('/')
def index():
    vms_data = be.print_all_vms()

    return render_template('index.html', vms=vms_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
