from flask import Flask, render_template
app = Flask(__name__)

from model import db   
import routes
import config

routes.init_routes(app)
config.apply_config(app)
db.init_app(app)

with app.app_context(): 
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
