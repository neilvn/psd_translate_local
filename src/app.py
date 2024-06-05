from controller import Translate_controller
from flask import Flask, make_response, render_template, request
# from utils import get_s3_item

BUCKET_NAME = 'ad-assembly-bucket112504-psd'

app = Flask(__name__)


@app.route('/')
def index():
    return make_response('Index', 200)


@app.route('/translate', methods=['GET'])
def translate():
    controller = Translate_controller()
    output = controller.extract()

    return str(output)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

