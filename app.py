from flask import Flask, render_template
from werkzeug.security import generate_password_hash
app = Flask(__name__)

from model import db, User  
import routes
import config

routes.init_routes(app)
config.apply_config(app)
db.init_app(app)

with app.app_context(): 
    db.create_all()
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin_user = User(
            full_name='System Admin', 
            username='admin',
            password_hash=generate_password_hash('admin123'),
            email='admin@hospital.com',
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
