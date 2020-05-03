from flask import Flask, render_template, Markup, request, session, url_for, redirect
from flask import make_response, flash
from flask_sqlalchemy import SQLAlchemy
import time

from sqlalchemy import null

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/wds'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# app.secret_key = 'hard to guess'

db = SQLAlchemy(app)

@app.route('/')
def index():
    username = request.cookies.get('email')
    if username in session:
        response = make_response(redirect('/insurance'))
        return response
    else:
        return redirect(url_for('login'), 302)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/login', methods=['POST', 'GET'])
def login():
    response = None
    if request.method == 'POST':
        login_email = request.form['email']
        login_password = request.form['password']
        login_user = User.query.filter_by(email=login_email, password=login_password).first()
        if login_user != None: # User exists
            check_list = request.form.getlist('admin')
            isAdmin = bool(check_list)
            if isAdmin: # Admin login
                admin_user = Admin.query.filter_by(u_id = login_user.u_id).first()
                if admin_user != None: # Admin account exists
                    session[login_email]='online'
                    response = make_response(redirect('/admin'))
                    response.set_cookie('login_time', time.strftime('%m-%d-%Y %H:%M:%S'))
                    response.set_cookie('email', login_email)
                    response.set_cookie('adminlogin', 'True')
                    return response
                else: # Admin account doesn't exist
                    flash('Admin does not exist!', 'error')
                    response = make_response(redirect('/login'))
                    return response

            else: # non-Admin login
                session[login_email]='online'
                response = make_response(redirect('/insurance'))
                response.set_cookie('login_time', time.strftime('%m-%d-%Y %H:%M:%S'))
                response.set_cookie('email', login_email)
                response.set_cookie('adminlogin', 'False')
                return response
        else: # User doesn't exist
            flash('Username or password incorrect!', 'error')
            response = make_response(redirect('/login'))
            return response

    elif request.method=='GET': 
        login_email = request.cookies.get('email')
        if login_email in session:
            login_time = request.cookies.get('login_time')
            # login_user = User.query.filter_by(email=login_email, password=login_password).first()
            # admin = Admin.query.filter_by(u_id=login_user.u_id).first()
            adminlogin = request.cookies.get('adminlogin')
            if adminlogin=='True':
                response = make_response(redirect('/admin'))
            elif adminlogin=='False':
                response = make_response(redirect('/insurance'))
            # response = make_response('Hello %s, you logged in on %s' % (username, login_time))
            return response
        else:
            title = request.args.get('title', 'User')
            response = make_response(render_template('login.html', title=title), 200)
            # response.headers['key'] = 'value'
            return response
    return response

@app.route('/logout')
def logout():
    email = request.cookies.get('email')
    if email != None:
        session.pop(email, None)
        response = make_response(redirect(url_for('login')))
        response.delete_cookie('login_time')
        response.delete_cookie('email')
        return response
    else:
        return redirect(url_for('login'))    

@app.route('/switchtoregister', methods=['POST', 'GET'])
def register():
    if request.method=='GET':
        # response = make_response(render_template('register.html'), 200)
        # return response
        return render_template('register.html')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        st_addr = request.form.get('st_addr')
        city = request.form.get('city')
        state = request.form.get('state')
        zipcode = request.form.get('zipcode')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        marital = request.form.get('marital')
        check_list = request.form.getlist('admin')
        isAdmin = bool(check_list)
        # if check_list!=None and check_list=='adminregister':
            # isAdmin = True
        # TODO: MD5 encryption on password

        u = User.query.filter_by(email=email).first()
        if u != None:
            flash('Email has already been registered!', 'error')
            print(1)
            return redirect('/switchtoregister')
        else:
            user = User(email, password)
            db.session.add(user)
            db.session.commit()
            customer = Customer(user.u_id, None, fname, lname, st_addr, city, state, zipcode, phone, gender, marital)
            db.session.add(customer)
            db.session.commit()
            if isAdmin:
                # This is an admin account
                admin = Admin(user.u_id)
                db.session.add(admin)
            flash('Register Succesfully!', 'message')
            response = make_response(redirect(url_for('index')))
            return response

@app.route('/test')
def test():
    customer = Customer(1, None, 'Y', 'B', '#@', 'New York', 'NY', '11201', '3243543522', 'M', 'S')
    db.session.add(customer)
    db.session.commit()

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=400):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code

@app.route('/exception')
def exception():
    app.logger.debug('Enter exception method')
    app.logger.error('403 error happened')
    raise InvalidUsage('No privilege to access the resource', status_code=403)

@app.route('/insurance')
def insurance():
    response = make_response(render_template('insurance.html'))
    return response

@app.route('/admin')
def adminpage():
    # allPlans = 
    response = make_response(render_template('admin.html'))
    return response

class User(db.Model):
    __tablename__='user'
    u_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(45), nullable=False, unique=True)
    password = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '%r %r %r' % (self.u_id, self.email, self.password)

    def __init__(self, email, password):
        self.email = email
        self.password = password

class Customer(db.Model):
    __tablename__='customer'
    u_id = db.Column(db.Integer, db.ForeignKey(User.u_id), primary_key=True)
    c_type = db.Column(db.String(1), nullable=True)
    fname = db.Column(db.String(30), nullable=False)
    lname = db.Column(db.String(30), nullable=False)
    st_addr = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zipcode = db.Column(db.String(5), nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    marital = db.Column(db.String(1), nullable=False)

    def __repr__(self):
        return '%r %r %r'%(self.u_id, self.c_type)
    
    def __init__(self, u_id, c_type, fname, lname, st_addr, city, state, zipcode, phone, gender, marital):
        self.u_id = u_id
        self.c_type=c_type
        self.fname = fname
        self.lname = lname
        self.st_addr=st_addr
        self.city = city
        self.state = state
        self.zipcode=zipcode
        self.phone = phone
        self.gender=gender
        self.marital = marital

class Admin(db.Model):
    __tablename__ = 'admin'
    u_id = db.Column(db.INT, db.ForeignKey('user.u_id'), primary_key=True)

    def __repr__(self):
        return '%r' % (self.u_id)

    def __init__(self, u_id):
        self.u_id = u_id

class Insurance(db.Model):
    __tablename__ = 'insurance'
    i_id = db.Column(db.INT, primary_key=True, autoincrement=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    i_amount = db.Column(db.Numeric(10, 2), nullable=False)
    i_status = db.Column(db.String(1), nullable=False)
    u_id = db.Column(db.INT, db.ForeignKey('customer.u_id'))

    def __repr__(self):
        return '%r %r %r %r %r %r' % (self.i_id, self.start_date, self.end_date, self.i_amount, self.i_status, self.c_id, self.c_type)

    def __init__(self, start_date, end_date, i_amount, i_status, c_id, c_type):
        self.start_date = start_date
        self.end_date = end_date
        self.i_amount = i_amount
        self.i_status = i_status
        self.c_id = c_id
        self.c_type = c_type

class Insurance_plan(db.model):
    __tablename__ = 'insurance_plan'
    p_id = db.Column(db.INT, primaty_key=True, autoincrement=True)
    deductible = db.Column(db.Numeric(10,2))
    description = db.Column(db.String(300))

    def __repr__(self):
        return '%r %r %r'%(self.p_id, self.deductible, self.description)
    
    def __init__(self, p_id, deductible, description)
        self.p_id=p_id
        self.deductible = deductible
        self.description = description

if __name__ == '__main__':
    app.run(debug=True)