from flask import Flask
from flask_cors import CORS

from exts import db

from cms import cms_bp
from front.views import wx_bp
import config

app = Flask(__name__)
app.config.from_object(config)
CORS(app, supports_credentials=True)

app.register_blueprint(cms_bp)
app.register_blueprint(wx_bp)

db.init_app(app)

if __name__ == '__main__':
    app.run(host="0.0.0.0")