from flask import Flask, render_template, Markup, request, session, url_for, redirect
from flask import make_response, flash
from flask_sqlalchemy import SQLAlchemy
import time

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess'
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:root@localhost:3306/wds'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True

db = SQLAlchemy(app)

# app.secret_key = 'hard to guess'

@app.route('/')
def index():
    username = request.cookies.get('myname')
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
        login_username = request.form['c_id']
        login_password = request.form['password']
        login_user = Customer.query.filter_by(c_id=login_username, password=login_password).first()
        if login_user != None:
            session[login_username]='online'
            response = make_response(redirect('/insurance'))
            response.set_cookie('login_time', time.strftime('%m-%d-%Y %H:%M:%S'))
            response.set_cookie('myname', login_username)
            return response
        else:
            flash('Username or password incorrect!', 'error')
            response = make_response(redirect('/login'))
            return response

    elif request.method=='GET': 
        username = request.cookies.get('myname')
        if username in session:
            login_time = request.cookies.get('login_time')
            # response = make_response('Hello %s, you logged in on %s' % (username, login_time))
            return redirect('/insurance')
        else:
            title = request.args.get('title', 'User')
            response = make_response(render_template('login.html', title=title), 200)
            # response.headers['key'] = 'value'
            return response
    return response

@app.route('/logout')
def logout():
    username = request.cookies.get('myname')
    if username!=None:
        session.pop(username, None)
        response = make_response(redirect(url_for('login')))
        response.delete_cookie('login_time')
        response.delete_cookie('myname')
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
        c_id = request.form.get('c_id')
        c_type = request.form.get('c_type')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        st_addr = request.form.get('st_addr')
        city = request.form.get('city')
        state = request.form.get('state')
        zipcode = request.form.get('zipcode')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        password = request.form.get('password')
        marital = request.form.get('marital')
        # TODO: MD5 encription on password

        c = Customer.query.filter_by(c_id = c_id).first()
        if c!=None:
            flash('User already existed!', 'error')
            return redirect('/switchtoregister')
        else: # user already existed
            customer = Customer(c_id, c_type, fname,lname, st_addr, city, state, zipcode, phone, gender, marital, password)
            db.session.add(customer)
            db.session.commit()

            response = make_response(redirect(url_for('index')))
            return response


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

class Customer(db.Model):
    __tablename__='customer'
    c_id = db.Column(db.String(10), primary_key=True)
    c_type = db.Column(db.String(1), primary_key=True)
    fname = db.Column(db.String(30), nullable=False)
    lname = db.Column(db.String(30), nullable=False)
    st_addr = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zipcode = db.Column(db.String(5), nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    marital = db.Column(db.String(1), nullable=False)
    # username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '%r %r %r'%(self.c_id, self.c_type, self.c_password)
    
    def __init__(self, c_id, c_type, fname,lname, st_addr, city, state, zipcode, phone, gender, marital, password):
        self.c_id = c_id
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
        self.password=password


if __name__ == '__main__':
    app.run(debug=True)