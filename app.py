from flask import Flask
from flask_cors import CORS

from exts import db, mail, scheduler

from cms.views import CMS_BPS
from front.views import FRONT_BPS
import config
import wtforms_json
import flask_whooshalchemyplus

app = Flask(__name__)
app.config.from_object(config)
CORS(app, supports_credentials=True)

for blueprint in CMS_BPS + FRONT_BPS:
    app.register_blueprint(blueprint)


db.init_app(app)
mail.init_app(app)
flask_whooshalchemyplus.init_app(app)
scheduler.init_app(app)
scheduler.start()

wtforms_json.init()


@app.route("/")
def index():
    return "success"


if __name__ == '__main__':
    # 测试分支，不稳定，有bug请联系我
    app.run(host="0.0.0.0")
    # from common.schedule import calculator_article_score
    # with app.app_context():
    #     calculator_article_score()
