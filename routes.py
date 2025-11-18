from flask import render_template,request,redirect, url_for,flash, session
from model import db, User
from werkzeug.security import generate_password_hash, check_password_hash



def init_routes(app):
    @app.route('/')
    def index():
        return render_template('register.html')
    
    @app.route('/patient-login')
    def patient_login():
        return render_template('patient-login.html')
    
    @app.route('/patient-login',methods=['POST'])
    def patient_login_post():
        username = request.form.get('username')
        password = request.form.get('password')  
        
        user= User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash,password):
            flash('Invalid username or password.')
            return redirect(url_for('patient_login'))
        
        session['user_id'] = user.id     
        session['role'] = 'patient'
        return redirect(url_for('patient_dashboard'))
    


    @app.route('/doctor-admin-login')
    def doctor_admin_login():
        return render_template('doctor-admin-login.html')   
    
    @app.route('/register')
    def register():      
        return render_template('register.html')                             
    
    @app.route('/patient-dashboard',methods=['GET','POST'])
    def patient_dashboard():    
        return render_template('patient.html') 


    @app.route('/admin-dashboard')
    def admin_dashboard():  
        return render_template('admin.html')    
    
    @app.route('/doctor-dashboard')
    def doctor_dashboard():  
        return render_template('doctor.html')
    
    @app.route('/register',methods=['POST'])
    def register_post():  
        username = request.form.get('username')
        password = request.form.get('password')  
        email= request.form.get('email')
        fullname= request.form.get('fullname')  
        confirm_password= request.form.get('confirm_password')
    
        if not username or not password or not email or not fullname or not confirm_password:
            flash('Please fill out all fields.')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.')        
            return redirect(url_for('register'))
        user= User.query.filter_by(username=username).first()

        if user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))
        
        password_hash= generate_password_hash(password)

        new_user= User(full_name=fullname,username=username,
                       email=email,password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('patient_login'))