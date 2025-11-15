from flask import Flask, render_template
app = Flask(__name__)

import model   
import routes
import config

routes.init_routes(app)
config.apply_config(app)



if __name__ == '__main__':
    app.run(debug=True)
