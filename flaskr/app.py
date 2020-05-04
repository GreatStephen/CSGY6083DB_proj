from flask import Flask, render_template, Markup, request, session, url_for, redirect
from flask import make_response, flash
from flask_sqlalchemy import SQLAlchemy
import time

from sqlalchemy import null

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:961112@localhost:3306/wds'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# app.secret_key = 'hard to guess'

db = SQLAlchemy(app)

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
        login_email = request.form['email']
        login_password = request.form['password']
        login_user = User.query.filter_by(email=login_email, password=login_password).first()
        if login_user != None:
            session[login_email]='online'
            admin = Admin.query.filter_by(u_id=login_user.u_id).first()
            if admin != None:
                response = make_response(redirect('/admin'))
            else:
                response = make_response(redirect('/insurance_home'))
            response.set_cookie('login_time', time.strftime('%m-%d-%Y %H:%M:%S'))
            response.set_cookie('email', login_email)
            return response
        else:
            flash('Username or password incorrect!', 'error')
            response = make_response(redirect('/login'))
            return response

    elif request.method=='GET': 
        login_email = request.cookies.get('email')
        if login_email in session:
            login_time = request.cookies.get('login_time')
            login_user = User.query.filter_by(email=login_email).first()
            admin = Admin.query.filter_by(u_id=login_user.u_id).first()
            if admin != None:
                response = make_response(redirect('/admin'))
            else:
                response = make_response(redirect('/insurance_home'))
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
        # TODO: MD5 encription on password

        u = User.query.filter_by(email=email).first()
        if u != None:
            flash('the email already registered!', 'error')
            print(1)
            return redirect('/switchtoregister')
        else:
            user = User(email, password)
            db.session.add(user)
            db.session.commit()
            customer = Customer(user.u_id, None, fname, lname, st_addr, city, state, zipcode, phone, gender, marital)
            db.session.add(customer)
            db.session.commit()

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

@app.route('/insurance_home', methods=['POST', 'GET'])
def insurance_home():
    if request.method == 'GET':
        response = make_response(render_template('insurance_home.html'))
    elif request.method == 'POST':
        deductible_lowest = int(request.form.get('deductible_lowest'))
        deductible_highest = int(request.form.get('deductible_highest'))
        annual_fee_lowest = int(request.form.get('annual_fee_lowest'))
        annual_fee_highest = int(request.form.get('annual_fee_highest'))
        home_num_lowest = int(request.form.get('home_num_lowest'))
        home_num_highest = int(request.form.get('home_num_highest'))
        policy = int(request.form.get('policy'))

        plan_home_list = Insurance_plan_home.query.filter_by(policy=policy).\
            filter(Insurance_plan_home.home_num.between(home_num_lowest, home_num_highest))
        p_id_list = []
        for plan in plan_home_list:
            p_id_list.append(plan.p_id)
        plan_list = Insurance_plan.query.filter(Insurance_plan.p_id.in_(p_id_list)).\
            filter(Insurance_plan.annual_fee.between(annual_fee_lowest, annual_fee_highest)).\
            filter(Insurance_plan.deductible.between(deductible_lowest, deductible_highest))
        p_id_list = []
        for plan in plan_list:
            p_id_list.append(plan.p_id)
        plan_home_list = Insurance_plan_home.query.filter(Insurance_plan_home.p_id.in_(p_id_list))

        list = []
        for ins_plan, ins_home_plan in zip(plan_list, plan_home_list):
            p = {}
            p['p_id'] = ins_plan.p_id
            p['deductible'] = ins_plan.deductible
            p['description'] = ins_plan.description
            p['annual_fee'] = ins_plan.annual_fee
            p['policy'] = ins_home_plan.policy
            p['home_num'] = ins_home_plan.home_num
            list.append(p)

        response = make_response(render_template('insurance_home.html', list=list))
    return response

@app.route('/payment/<p_id>', methods=['POST', 'GET'])
def payment(p_id):
    print(p_id)
    if request.method == 'GET':
        response = make_response(render_template('payment.html', p_id=p_id))
    elif request.method == 'POST':
        pass
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
        return '%r %r %r %r %r %r %r %r %r %r %r' % \
               (self.u_id, self.c_type, self.fname, self.lname, self.st_addr, self.city,
                self.state, self.zipcode, self.phone, self.gender, self.marital)
    
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
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), primary_key=True)

    def __repr__(self):
        return '%r' % (self.u_id)

    def __init__(self, u_id):
        self.u_id = u_id

class Home(db.Model):
    __tablename__ = 'home'
    h_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    purchase_date = db.Column(db.Date, nullable=False)
    purchase_value = db.Column(db.Numeric(10, 2), nullable=False)
    area = db.Column(db.Numeric(10, 2), nullable=False)
    h_type = db.Column(db.String(1), nullable=False)
    afn = db.Column(db.String(1), nullable=False)
    hs = db.Column(db.String(1), nullable=False)
    sp = db.Column(db.String(1), nullable=True)
    bsm = db.Column(db.String(1), nullable=False)

    def __repr__(self):
        return '%r %r %r %r %r %r %r %r %r' % \
               (self.h_id, self.purchase_date, self.purchase_value, self.area,
                self.h_type, self.afn, self.hs, self.sp, self.bsm)

    def __init__(self, h_id, purchase_date, purchase_value, area, h_type, afn, hs, sp, bsm):
        self.h_id = h_id
        self.purchase_date = purchase_date
        self.purchase_value = purchase_value
        self.area = area
        self.h_type = h_type
        self.afn =  afn
        self.hs = hs
        self.sp = sp
        self.bsm = bsm

class Home_insured(db.Model):
    __tablename__ = 'home_insured'
    i_id = db.Column(db.Integer, db.ForeignKey('insurance_home.i_id'), primary_key=True)
    h_id = db.Column(db.Integer, db.ForeignKey('home.h_id'), primary_key=True)

    def __repr__(self):
        return '%r %r' & (self.i_id, self.h_id)

    def __init__(self, i_id, h_id):
        self.i_id = i_id
        self.h_id = h_id

class Insurance(db.Model):
    __tablename__ = 'insurance'
    i_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    i_amount = db.Column(db.Numeric(10, 2), nullable=False)
    i_status = db.Column(db.String(1), nullable=False)
    u_id = db.Column(db.INT, db.ForeignKey('customer.u_id'))

    def __repr__(self):
        return '%r %r %r %r %r %r' % \
               (self.i_id, self.start_date, self.end_date, self.i_amount, self.i_status, self.u_id)

    def __init__(self, start_date, end_date, i_amount, i_status, u_id):
        self.start_date = start_date
        self.end_date = end_date
        self.i_amount = i_amount
        self.i_status = i_status
        self.u_id = u_id

class Insurance_home(db.Model):
    __tablename__ = 'insurance_home'
    i_id = db.Column(db.Integer, db.ForeignKey('insurance.i_id'), primary_key=True)
    p_id = db.Column(db.Integer, db.ForeignKey('insurance_home_plan.p_id'), nullable=False)

    def __repr__(self):
        return '%r %r' % (self.i_id, self.p_id)

    def __init__(self, i_id, p_id):
        self.i_id = i_id
        self.p_id = p_id

class Insurance_auto(db.Model):
    __tablename__ = 'insurance_auto'
    i_id = db.Column(db.Integer, db.ForeignKey('insurance.i_id'), primary_key=True)
    p_id = db.Column(db.Integer, db.ForeignKey('insurance_auto_plan.p_id'), nullable=False)

    def __repr__(self):
        return '%r %r' % (self.i_id, self.p_id)

    def __init__(self, i_id, p_id):
        self.i_id = i_id
        self.p_id = p_id

class Insurance_plan(db.Model):
    __tablename__ = 'insurance_plan'
    p_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.String(300), nullable=False)
    deductible = db.Column(db.Numeric(10, 2), nullable=False)
    annual_fee = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return '%r %r %r %r' % (self.p_id, self.description, self.deductible, self.annual_fee)

    def __init__(self, p_id, description, deductible, annual_fee):
        self.p_id = p_id
        self.description = description
        self.deductible = deductible
        self.annual_fee = annual_fee

class Insurance_plan_home(db.Model):
    __tablename__ = 'insurance_plan_home'
    p_id = db.Column(db.Integer, db.ForeignKey('insurance_plan.p_id'), primary_key=True)
    policy = db.Column(db.Integer, nullable=False)
    home_num = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '%r %r %r' % (self.p_id, self.policy, self.home_num)

    def __init__(self, p_id, policy, home_num):
        self.p_id = p_id
        self.policy = policy
        self.home_num = home_num

class Insurance_plan_auto(db.Model):
    __tablename__ = 'insurance_plan_auto'
    p_id = db.Column(db.Integer, db.ForeignKey('insurance_plan.p_id'), primary_key=True)
    model = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return '%r %r' % (self.p_id, self.model)

    def __init__(self, p_id, model):
        self.p_id = p_id
        self.model = model

if __name__ == '__main__':
    app.run(debug=True)