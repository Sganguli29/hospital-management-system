from flask import render_template


def init_routes(app):
    @app.route('/')
    def index():
        return render_template('register.html')
    
    @app.route('/patient-login')
    def patient_login():
        return render_template('patient-login.html')
    
    @app.route('/doctor-admin-login')
    def doctor_admin_login():
        return render_template('doctor-admin-login.html')   
    
    @app.route('/register')
    def register():      
        return render_template('register.html')                             
    
    @app.route('/patient-dashboard')
    def patient_dashboard():    
        return render_template('patient.html')  
    @app.route('/admin-dashboard')
    def admin_dashboard():  
        return render_template('admin.html')    
    
