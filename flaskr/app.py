from flask import Flask, render_template, Markup, request, session, url_for, redirect
from flask import make_response, flash
from flask_sqlalchemy import SQLAlchemy
import time
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from sqlalchemy import null

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/wds'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config.update(
    # SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# app.secret_key = 'hard to guess'

db = SQLAlchemy(app)

@app.route('/')
def index():
    username = request.cookies.get('email')
    if username in session:
        admin = request.cookies.get('adminlogin')
        if admin == 'False':
            response = make_response(redirect('/insurance'))
        elif admin == 'True':
            response = make_response(redirect('/admin'))
        return response
    else:
        response = make_response(redirect(url_for('login'), 302))
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

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
        #login_user = User.query.filter_by(email=login_email, password=login_password).first()
        login_user = User.query.filter_by(email=login_email).first()
        if login_user != None: # User exists
            if not login_user.check_password(login_password):
                flash('Username or password incorrect!', 'error')
                response = make_response(redirect('/login'))
                return response
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
        if gender == "":
            gender = None
        marital =request.form.get('marital')
        check_list = request.form.getlist('admin')
        isAdmin = bool(check_list)
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

@app.route('/insurance', methods=['POST', 'GET'])
@app.route('/insurance/<type>', methods=['POST', 'GET'])
def insurance(type=None):
    if request.method == 'GET':
        list = []
        email = request.cookies.get('email')
        if email==None:
            flash('Please login first!', 'error')
            return redirect('/login')
        user = User.query.filter_by(email=email).first()
        u_id = user.u_id
        ins_list = Insurance.query.filter_by(u_id=u_id).all()

        ins_id_list = []
        for ins in ins_list:
            ins_id_list.append(ins.i_id)

        home_ins_list = Insurance_home.query.filter(Insurance_home.i_id.in_(ins_id_list)).all()
        auto_ins_list = Insurance_auto.query.filter(Insurance_auto.i_id.in_(ins_id_list)).all()

        home_ins_id_list = []
        for ins in home_ins_list:
            home_ins_id_list.append(ins.i_id)
        auto_ins_id_list = []
        for ins in auto_ins_list:
            auto_ins_id_list.append(ins.i_id)

        for ins in ins_list:
            item = {}
            item['i_id'] = ins.i_id
            item['start_date'] = ins.start_date
            item['end_date'] = ins.end_date
            item['amount'] = ins.i_amount
            item['status'] = ins.i_status
            item['u_id'] = ins.u_id
            if ins.i_id in home_ins_id_list:
                item['type'] = 'Home'
                for h_ins in home_ins_list:
                    if h_ins.i_id == ins.i_id:
                        item['p_id'] = h_ins.p_id
            else:
                item['type'] = 'Auto'
                for a_ins in auto_ins_list:
                    if a_ins.i_id == ins.i_id:
                        item['p_id'] = a_ins.p_id
            list.append(item)
            print(item)

        response = make_response(render_template('insurance.html', list=list))
    elif request.method == 'POST':
        pass
    return response

@app.route('/insurance_home', methods=['POST', 'GET'])
def insurance_home():
    policy_list = [
        '',
        'HO-1 (Basic)',
        'HO-2 (Broad)',
        'HO-3 (All Risk)',
        'HO-4 (Renter’s)',
        'HO-5 (Comprehensive)',
        'HO-6 (Condominium Coverage)',
        'HO-7 (Mobile Home)',
        'HO-8 (Older Home)',
        'Dwelling Fir',
        'Home Owner Insurance'
    ]
    filters = {}

    if request.method == 'GET':
        response = make_response(render_template('insurance_home.html', policy_list=policy_list))
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

        filters['deductible_lowest'] = deductible_lowest
        filters['deductible_highest'] = deductible_highest
        filters['annual_fee_lowest'] = annual_fee_lowest
        filters['annual_fee_highest'] = annual_fee_highest
        filters['home_num_lowest'] = home_num_lowest
        filters['home_num_highest'] = home_num_highest
        filters['policy'] = policy

        response = make_response(
            render_template('insurance_home.html', list=list, filters=filters, policy_list=policy_list)
        )

    return response

@app.route('/insurance_auto', methods=['POST', 'GET'])
def insurance_auto():
    model_list = [
        '',
        'Small Family Car',
        'Car Derived Van',
        'Sport Utility Vehicle',
        'Multi-Purpose Vehicle',
        'Coupe',
        'Roadster',
        'Cabrio',
        'Crossover',
        'Pickup',
        'Car Utility',
        'Wagon'
    ]
    filters = {}

    if request.method == 'GET':
        response = make_response(render_template('insurance_auto.html', model_list=model_list))
    elif request.method == 'POST':
        deductible_lowest = int(request.form.get('deductible_lowest'))
        deductible_highest = int(request.form.get('deductible_highest'))
        annual_fee_lowest = int(request.form.get('annual_fee_lowest'))
        annual_fee_highest = int(request.form.get('annual_fee_highest'))
        vehicle_num_lowest = int(request.form.get('vehicle_num_lowest'))
        vehicle_num_highest = int(request.form.get('vehicle_num_highest'))
        model = int(request.form.get('model'))

        plan_auto_list = Insurance_plan_auto.query.filter_by(model=model).\
            filter(Insurance_plan_auto.vehicle_num.between(vehicle_num_lowest, vehicle_num_highest))
        p_id_list = []
        for plan in plan_auto_list:
            p_id_list.append(plan.p_id)
        plan_list = Insurance_plan.query.filter(Insurance_plan.p_id.in_(p_id_list)).\
            filter(Insurance_plan.annual_fee.between(annual_fee_lowest, annual_fee_highest)).\
            filter(Insurance_plan.deductible.between(deductible_lowest, deductible_highest))
        p_id_list = []
        for plan in plan_list:
            p_id_list.append(plan.p_id)
        plan_auto_list = Insurance_plan_auto.query.filter(Insurance_plan_auto.p_id.in_(p_id_list))

        list = []
        for ins_plan, ins_auto_plan in zip(plan_list, plan_auto_list):
            p = {}
            p['p_id'] = ins_plan.p_id
            p['deductible'] = ins_plan.deductible
            p['description'] = ins_plan.description
            p['annual_fee'] = ins_plan.annual_fee
            p['model'] = model_list[ins_auto_plan.model]
            p['vehicle_num'] = ins_auto_plan.vehicle_num
            list.append(p)

        filters['deductible_lowest'] = deductible_lowest
        filters['deductible_highest'] = deductible_highest
        filters['annual_fee_lowest'] = annual_fee_lowest
        filters['annual_fee_highest'] = annual_fee_highest
        filters['vehicle_num_lowest'] = vehicle_num_lowest
        filters['vehicle_num_highest'] = vehicle_num_highest
        filters['model'] = model

        response = make_response(
            render_template('insurance_auto.html', list=list, filters=filters, model_list=model_list)
        )
    return response

@app.route('/info_home', methods=['POST', 'GET'])
def info_home():
    if request.method == 'GET':
        p_id = request.args.get('p_id')
        p = Insurance_plan.query.filter_by(p_id=p_id).first()
        p_h = Insurance_plan_home.query.filter_by(p_id=p_id).first()
        plan = {}
        plan['p_id'] = p_id
        plan['type'] = 'Home'
        plan['deductible'] = p.deductible
        plan['description'] = p.description
        plan['annual_fee'] = p.annual_fee
        plan['home_num'] = p_h.home_num
        plan['policy'] = p_h.policy
        response = make_response(render_template('info_home.html', plan=plan))
    elif request.method == 'POST':
        p_id = request.form.get('p_id')
        p = Insurance_plan.query.filter_by(p_id=p_id).first()
        p_h = Insurance_plan_home.query.filter_by(p_id=p_id).first()
        plan = {}
        plan['p_id'] = p_id
        plan['type'] = 'Home'
        plan['deductible'] = p.deductible
        plan['description'] = p.description
        plan['annual_fee'] = p.annual_fee
        plan['home_num'] = p_h.home_num
        plan['policy'] = p_h.policy

        home_list = []
        for i in range(p_h.home_num):
            home = {}
            home['purchase_date'] = request.form.get('purchase_date_'+str(i))
            home['purchase_value'] = request.form.get('purchase_value_'+str(i))
            home['area'] = request.form.get('area_'+str(i))
            home['h_type'] = request.form.get('h_type_'+str(i))
            # home[''] = request.form.get('purchase_value_'+str(i))
            home['afn'] = request.form.get('afn_'+str(i))
            home['hss'] = request.form.get('hss_'+str(i))
            home['sp'] = request.form.get('sp_'+str(i))
            home['bsm'] = request.form.get('bs_'+str(i))
            home_list.append(home)
        print(home_list)

        # Insert into Insurance table
        email = request.cookies.get('email')
        if email==None:
            flash('Please login first!', 'error')
            return redirect('/login')
        user = User.query.filter_by(email = email).first()
        u_id = None
        if user!=None:
            u_id = user.u_id
        else:
            flash('Please login first!', 'error')
            return redirect('/login')
        start_date = time.strftime('%Y-%m-%d')
        end_date = datetime.now()
        # d = timedelta(years=1)
        end_date = (end_date+relativedelta(years=1)).strftime('%Y-%m-%d')
        i_amount = plan['annual_fee']
        i_status = 'C'

        ins = Insurance(start_date, end_date, i_amount, i_status, u_id)
        db.session.add(ins)
        db.session.commit()

        # Insert into Insurance_home table
        ins_h = Insurance_home(ins.i_id, plan['p_id'])
        db.session.add(ins_h)
        db.session.commit()

        # Insert into Home table & Home_insured table
        for home in home_list:
            if home['afn'] == 'on':
                home['afn']=1
            else:
                home['afn']=0
            if home['hss']=='on':
                home['hss']=1
            else:
                home['hss']=0
            if home['bsm']=='on':
                home['bsm']=1
            else:
                home['bsm']=0
            if home['sp']=='null':
                home['sp']=None
            
            h = Home(None, home['purchase_date'], home['purchase_value'], home['area'], home['h_type'], home['afn'], home['hss'], home['sp'], home['bsm'])
            db.session.add(h)
            db.session.commit()

            h_i = Home_insured(ins.i_id, h.h_id)
            db.session.add(h_i)
            db.session.commit()

        # Insert into Invoice table
        time_now = datetime.now()
        inv_date = time_now.strftime('%Y-%m-%d')
        payment_due_date = (time_now+relativedelta(years=1)).strftime('%Y-%m-%d')
        inv_amount = plan['annual_fee']

        invoice = Invoice(None, inv_date, payment_due_date, inv_amount)
        db.session.add(invoice)
        db.session.commit()

        # Insert into Invoice_home table
        inv_h = Invoice_home(invoice.inv_id, ins.i_id)
        db.session.add(inv_h)
        db.session.commit()

        # update customer type
        user = User.query.filter_by(email=request.cookies.get('email')).first()
        customer = Customer.query.filter_by(u_id=user.u_id).first()
        if customer is not None:
            if customer.c_type == "A":
                customer.c_type = "B"
            elif customer.c_type is None:
                customer.c_type = "H"
        db.session.commit()


        # response = make_response(redirect(url_for('payment', i_id=ins.i_id, inv_id=inv_h.inv_id, type = 'home')))
        response = make_response(render_template('payment.html', isPaid='False', i_id=ins.i_id, inv_id=inv_h.inv_id, type='home', annual_fee=ins.i_amount))
        #response = make_response(render_template('payment.html', p_id=p_id, plan=plan, home_list=home_list))
    return response

@app.route('/info_auto', methods=['POST', 'GET'])
def info_auto():
    if request.method == 'GET':
        p_id = request.args.get('p_id')
        p = Insurance_plan.query.filter_by(p_id=p_id).first()
        p_a = Insurance_plan_auto.query.filter_by(p_id=p_id).first()
        plan = {}
        plan['p_id'] = p_id
        plan['type'] = 'Home'
        plan['deductible'] = p.deductible
        plan['description'] = p.description
        plan['annual_fee'] = p.annual_fee
        plan['vehicle_num'] = p_a.vehicle_num
        plan['model'] = p_a.model
        response = make_response(render_template('info_auto.html', plan=plan))
    elif request.method == 'POST':
        p_id = request.form.get('p_id')
        p = Insurance_plan.query.filter_by(p_id=p_id).first()
        p_a = Insurance_plan_auto.query.filter_by(p_id=p_id).first()
        plan = {}
        plan['p_id'] = p_id
        plan['type'] = 'Auto'
        plan['deductible'] = p.deductible
        plan['description'] = p.description
        plan['annual_fee'] = p.annual_fee
        plan['vehicle_num'] = p_a.vehicle_num
        plan['model'] = p_a.model

        auto_list = []
        for i in range(p_a.vehicle_num):
            auto = {}
            auto['mmy'] = request.form.get('mmy_'+str(i))
            auto['vin'] = request.form.get('vin_'+str(i))
            auto['v_status'] = request.form.get('v_status_'+str(i))
            auto['drivers'] = []
            auto['drivers'].append(request.form.get('license_number_'+str(i)+'_1'))
            for j in range(2, 6):
                ln = request.form.get('license_number_'+str(i)+'_'+str(j))
                if len(ln)==9:
                    auto['drivers'].append(ln)
            print(auto['drivers'])
            auto_list.append(auto)
        # response = make_response(redirect(url_for('payment', p_id=p_id, plan=plan, auto_list=auto_list)))
        # return response
        #response = make_response(render_template('payment.html', p_id=p_id, plan=plan, auto_list=auto_list))

        # Insert into Insurance table
        email = request.cookies.get('email')
        if email==None:
            flash('Please login first!', 'error')
            return redirect('/login')
        user = User.query.filter_by(email = email).first()
        u_id = None
        if user!=None:
            u_id = user.u_id
        else:
            flash('Please login first!', 'error')
            return redirect('/login')
        start_date = time.strftime('%Y-%m-%d')
        end_date = datetime.now()
        end_date = (end_date+relativedelta(years=1)).strftime('%Y-%m-%d')
        i_amount = plan['annual_fee']
        i_status = 'C'

        ins = Insurance(start_date, end_date, i_amount, i_status, u_id)
        db.session.add(ins)
        db.session.commit()

        # Insert into Insurance_auto table
        ins_a = Insurance_auto(ins.i_id, plan['p_id'])
        db.session.add(ins_a)
        db.session.commit()

        # Insert into Vehicle & Vehicle_insured & Drivers & Vehicle_driver table
        for auto in auto_list:
            vin = auto['vin']
            mmy = auto['mmy']
            v_status = auto['v_status']

            vehicle = Vehicle(vin, mmy, v_status)
            db.session.add(vehicle)
            db.session.commit()

            drivers = auto['drivers']
            for ln in drivers:
                license_number = ln
                fname = 'fname'
                lname = 'lname'
                birthday = datetime.now().strftime('%Y-%m-%d')
                drivers = Drivers(license_number, fname, lname, birthday)
                db.session.add(drivers)
                db.session.commit()

                vehicle_driver = Vehicle_driver(license_number, vin)
                db.session.add(vehicle_driver)
                db.session.commit()
            
            vehicle_insured = Vehicle_insured(ins.i_id, vin)
            db.session.add(vehicle_insured)
            db.session.commit()

        # Insert into Invoice table
        time_now = datetime.now()
        inv_date = time_now.strftime('%Y-%m-%d')
        payment_due_date = (time_now+relativedelta(years=1)).strftime('%Y-%m-%d')
        inv_amount = plan['annual_fee']

        invoice = Invoice(None, inv_date, payment_due_date, inv_amount)
        db.session.add(invoice)
        db.session.commit()

        # Insert into Invoice_auto table
        inv_a = Invoice_auto(invoice.inv_id, ins.i_id)
        db.session.add(inv_a)
        db.session.commit()

        # update customer type
        user = User.query.filter_by(email=request.cookies.get('email')).first()
        customer = Customer.query.filter_by(u_id=user.u_id).first()
        if customer is not None:
            if customer.c_type == "H":
                customer.c_type = "B"
            elif customer.c_type is None:
                customer.c_type = "A"
        db.session.commit()

        response = make_response(render_template('payment.html', isPaid='False', i_id=ins.i_id, inv_id=inv_a.inv_id, type = 'auto', annual_fee=ins.i_amount))

    return response

@app.route('/payment', methods=['POST', 'GET'])
def payment():
    if request.method == 'GET':
        i_id = request.args.get('i_id')
        p_id = request.args.get('p_id')
        inv_h = Invoice_home.query.filter_by(i_id=i_id).first()
        if inv_h!=None:
            inv_id = inv_h.inv_id
            p_h = Payment_home.query.filter_by(inv_id = inv_id).all()
            if p_h!=None and len(p_h)>0:
                # Show the payments
                p_list=[]
                for p_h_item in p_h:
                    p_item = Payment.query.filter_by(p_id=p_h_item.p_id).first()
                    p={}
                    p['p_id']=p_item.p_id
                    p['p_date']=p_item.p_date
                    p['method']=p_item.method
                    p['p_amount']=p_item.p_amount
                    p_list.append(p)
                response = make_response(render_template('payment.html', isPaid='True', p_list = p_list))
                return response
            else:
                # Have not paid. Redirect to 'payment.html' with parameters.
                ins = Insurance.query.filter_by(i_id=i_id).first()
                response = make_response(render_template('payment.html', isPaid='False', i_id=i_id, inv_id=inv_id, type='home', annual_fee=ins.i_amount))
                return response
        else:
            inv_a = Invoice_auto.query.filter_by(i_id=i_id).first()
            inv_id = inv_a.inv_id
            p_a = Payment_auto.query.filter_by(inv_id=inv_id).all()
            if p_a!=None and len(p_a)>0:
                p_list=[]
                for p_a_item in p_a:
                    p_item = Payment.query.filter_by(p_id=p_a_item.p_id).first()
                    p={}
                    p['p_id']=p_item.p_id
                    p['p_date']=p_item.p_date
                    p['method']=p_item.method
                    p['p_amount']=p_item.p_amount
                    p_list.append(p)
                response = make_response(render_template('payment.html', isPaid='True', p_list = p_list))
                return response
            else:
                # Have not paid. Redirect to 'payment.html' with parameters.
                ins = Insurance.query.filter_by(i_id=i_id).first()
                response = make_response(render_template('payment.html', isPaid='False', i_id=i_id, inv_id=inv_id, type='auto', annual_fee=ins.i_amount))
                return response

            return "done"

    elif request.method == 'POST':
        i_id = request.form.get('i_id')
        inv_id = request.form.get('inv_id')
        type = request.form.get('type')
        annual_fee = request.form.get('annual_fee')
        installment = request.form.get('installment')
        pay_method = request.form.get('method')
        # TODO: Generate payments & payment_home
        if installment=='1':
            num=1
        elif installment=='3':
            num=3
        elif installment=='6':
            num=6
        fee_per_installment = float(annual_fee)/num
        
        for i in range(num):
            sysdate = datetime.now().strftime('%Y-%m-%d')
            pay = Payment(None, sysdate, pay_method, fee_per_installment)
            db.session.add(pay)
            db.session.commit()

            if type=='home':
                p_h = Payment_home(pay.p_id, inv_id, i_id)
                db.session.add(p_h)
                db.session.commit()
            elif type=='auto':
                p_a = Payment_auto(pay.p_id, inv_id, i_id)
                db.session.add(p_a)
                db.session.commit()
        response = make_response(redirect(url_for('insurance')));
        return response

@app.route('/admin')
def adminpage():
    allPlans = Insurance_plan.query.all();
    # print(allPlans)
    for i in range(0, len(allPlans)):
        str = allPlans[i].__repr__()
        items = str.split('/')
        print(items)
        if len(items)==4:
            description = items[1]
            items[1]=description[1:-1:1]
            deductible = items[2]
            items[2]=deductible[deductible.index('(')+2:deductible.index(')')-1:1]
            annual_fee = items[3]
            items[3]=annual_fee[annual_fee.index('(')+2:annual_fee.index(')')-1:1]
        allPlans[i]=items

    print(len(allPlans))
    print(type(allPlans))
    print(allPlans)
    response = make_response(render_template('admin.html', allPlans = allPlans))
    return response

@app.route('/admin/modify', methods=['POST'])
def admin_modify():
    if request.method=='POST':
        action = request.form.get('action')
        str = action.split(' ')
        print(str[0])
        if str[0]=='addnew':
            return render_template('modify_addnew.html', title=str[0]);
        elif str[0]=='delete':
            p_id=str[1]
            ipa = Insurance_plan_auto.query.filter_by(p_id=p_id).first()
            if ipa!=None:
                db.session.delete(ipa)
                db.session.commit()

            iph = Insurance_plan_home.query.filter_by(p_id=p_id).first()
            if iph!=None:
                db.session.delete(iph)
                db.session.commit()

            ip = Insurance_plan.query.filter_by(p_id=p_id).first()
            if ip!=None:
                db.session.delete(ip)
                db.session.commit()
            response = make_response(redirect('/admin'))
            return response
        elif str[0]=='update':
            p_id=str[1]
            ip = Insurance_plan.query.filter_by(p_id=p_id).first()
            if ip!= None:
                ip_str = ip.__repr__().split('/')
                description = ip_str[1]
                ip_str[1]=description[1:-1:1]
                deductible = ip_str[2]
                ip_str[2]=deductible[deductible.index('(')+2:deductible.index(')')-1:1]
                annual_fee = ip_str[3]
                ip_str[3]=annual_fee[annual_fee.index('(')+2:annual_fee.index(')')-1:1]

            mytype = 'none'
            ipa = Insurance_plan_auto.query.filter_by(p_id=p_id).first()
            if ipa!=None:
                mytype='auto'
                ipa_str = ipa.__repr__().split(' ')
                response = make_response(render_template('modify_update.html', title=str[0], mytype=mytype, ip=ip_str, ipa=ipa_str, iph=None))
                return response
            else:
                iph = Insurance_plan_home.query.filter_by(p_id=p_id).first()
                if iph!=None:
                    mytype='home'
                    iph_str=iph.__repr__().split(' ')
                    response = make_response(render_template('modify_update.html', title=str[0], mytype=mytype, ip=ip_str, ipa=None, iph=iph_str))
                    return response
        return 'Error'

@app.route('/admin/modify_addnew', methods=['POST'])
def modify_addnew():
    print('this')
    if request.method=='POST':
        
        p_id=0
        deductible = request.form.get('deductible')
        description = request.form.get('description')
        annual_fee = request.form.get('annual_fee')
        insurance_plan = Insurance_plan(None,description, deductible, annual_fee)
        db.session.add(insurance_plan)
        db.session.commit()

        mytype = request.form.get('type')
        if mytype=='auto':
            vehicle_num = request.form.get('vehicle_num')
            model = request.form.get('model')
            insurance_plan_auto = Insurance_plan_auto(insurance_plan.p_id, vehicle_num, model)
            db.session.add(insurance_plan_auto)
            db.session.commit()
        elif mytype=='home':
            policy = request.form.get('policy')
            home_num = request.form.get('home_number')
            insurance_plan_home = Insurance_plan_home(insurance_plan.p_id, policy, home_num)
            db.session.add(insurance_plan_home)
            db.session.commit()
        
        response = make_response(redirect('/admin'));
        return response

@app.route('/admin/modify_update', methods=['POST'])
def modify_update():
    # return "update success"
    p_id = request.form.get('p_id')
    print("p_id=",p_id)
    type = request.form.get('mytype')
    description = request.form.get('description')
    deductible = request.form.get('deductible')
    annual_fee = request.form.get('annual_fee')
    ip = Insurance_plan.query.filter_by(p_id=p_id).first()
    if ip!=None:
        ip.description = description
        ip.deductible = deductible
        ip.annual_fee = annual_fee
        db.session.commit()
    if type=='auto':
        ipa = Insurance_plan_auto.query.filter_by(p_id=p_id).first()
        vehicle_num = request.form.get('vehicle_num')
        model = request.form.get('model')
        ipa.vehicle_num = vehicle_num
        ipa.model = model
        db.session.commit()
    elif type=='home':
        iph = Insurance_plan_home.query.filter_by(p_id=p_id).first()
        policy = request.form.get('policy')
        home_number = request.form.get('home_number')
        iph.policy = policy
        iph.home_num = home_number
        db.session.commit()

    response = make_response(redirect('/admin'))
    return response



class User(db.Model):
    __tablename__='user'
    u_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(45), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    #password = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '%r %r %r' % (self.u_id, self.email, self.password)

    def __init__(self, email, password):
        self.email = email
        self.password = password

    @property
    def password(self):
        raise AttributeError('User Password is not allowed to read.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    hss = db.Column(db.String(1), nullable=False)
    sp = db.Column(db.String(1), nullable=True)
    bsm = db.Column(db.String(1), nullable=False)

    def __repr__(self):
        return '%r %r %r %r %r %r %r %r %r' % \
                (self.h_id, self.purchase_date, self.purchase_value, self.area,
                self.h_type, self.afn, self.hss, self.sp, self.bsm)

    def __init__(self, h_id, purchase_date, purchase_value, area, h_type, afn, hss, sp, bsm):
        self.h_id = h_id
        self.purchase_date = purchase_date
        self.purchase_value = purchase_value
        self.area = area
        self.h_type = h_type
        self.afn =  afn
        self.hss = hss
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
    p_id = db.Column(db.Integer, db.ForeignKey('insurance_plan_home.p_id'), nullable=False)

    def __repr__(self):
        return '%r %r' % (self.i_id, self.p_id)

    def __init__(self, i_id, p_id):
        self.i_id = i_id
        self.p_id = p_id

class Insurance_auto(db.Model):
    __tablename__ = 'insurance_auto'
    i_id = db.Column(db.Integer, db.ForeignKey('insurance.i_id'), primary_key=True)
    p_id = db.Column(db.Integer, db.ForeignKey('insurance_plan_auto.p_id'), nullable=False)

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
        return '%r/%r/%r/%r' % (self.p_id, self.description, self.deductible, self.annual_fee)

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
    model = db.Column(db.Integer, nullable=False)
    vehicle_num = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '%r %r %r' % (self.p_id, self.vehicle_num, self.model)

    def __init__(self, p_id, vehicle_num, model):
        self.p_id = p_id
        self.vehicle_num = vehicle_num
        self.model = model

class Invoice(db.Model):
    __tablename__ = 'invoice'
    inv_id = db.Column(db.Integer, primary_key=True)
    inv_date = db.Column(db.Date, nullable=False)
    payment_due_date = db.Column(db.Date, nullable=False)
    inv_amount = db.Column(db.Numeric(10,2), nullable=False)

    def __repr__(self):
        return '%r %r %r %r' % (self.inv_id, self.inv_date, self.payment_due_date, self.inv_amount)

    def __init__(self, inv_id, inv_date, payment_due_date, inv_amount):
        self.inv_id = inv_id
        self. inv_date = inv_date
        self.payment_due_date = payment_due_date
        self.inv_amount = inv_amount

class Invoice_home(db.Model):
    __tablename__ = 'invoice_home'
    inv_id = db.Column(db.Integer, db.ForeignKey('invoice.inv_id'), primary_key=True)
    i_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '%r %r' % (self.inv_id, self.i_id)
    
    def __init__(self, inv_id, i_id):
        self.inv_id = inv_id
        self.i_id = i_id

class Invoice_auto(db.Model):
    __tablename__ = 'invoice_auto'
    inv_id = db.Column(db.Integer, db.ForeignKey('invoice.inv_id'), primary_key=True)
    i_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '%r %r' % (self.inv_id, self.i_id)
    
    def __init__(self, inv_id, i_id):
        self.inv_id = inv_id
        self.i_id = i_id

class Payment(db.Model):
    __tablename__ = 'payment'
    p_id = db.Column(db.Integer, primary_key=True)
    p_date = db.Column(db.Date, nullable=False)
    method = db.Column(db.String(6), nullable=False)
    p_amount = db.Column(db.Numeric(10,2), nullable=False)

    def __repr__(self):
        return '%r %r %r %r' % (self.p_id, self.p_date, self.method, self.p_amount)
    
    def __init__(self, p_id, p_date, method, p_amount):
        self.p_id = p_id
        self.p_date = p_date
        self.method = method
        self.p_amount= p_amount

class Payment_home(db.Model):
    __tablename__ = 'payment_home'
    p_id = db.Column(db.Integer, primary_key=True)
    inv_id = db.Column(db.Integer, db.ForeignKey('invoice_home.inv_id'), nullable=False)
    i_id = db.Column(db.Integer, db.ForeignKey('insurance_home.i_id'), nullable=False)

    def __repr__(self):
        return '%r %r %r' % (self.p_id, self.inv_id, self.i_id)
    
    def __init__(self, p_id, inv_id, i_id):
        self.p_id = p_id
        self.inv_id = inv_id
        self.i_id = i_id

class Payment_auto(db.Model):
    __tablename__ = 'payment_auto'
    p_id = db.Column(db.Integer, primary_key=True)
    inv_id = db.Column(db.Integer, db.ForeignKey('invoice_auto.inv_id'), nullable=False)
    i_id = db.Column(db.Integer, db.ForeignKey('insurance_auto.i_id'), nullable=False)

    def __repr__(self):
        return '%r %r %r' % (self.p_id, self.inv_id, self.i_id)
    
    def __init__(self, p_id, inv_id, i_id):
        self.p_id = p_id
        self.inv_id = inv_id
        self.i_id = i_id

class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    vin = db.Column(db.String(17), primary_key=True)
    mmy = db.Column(db.String(4), nullable=False)
    v_status = db.Column(db.String(1), nullable=False)

    def __repr__(self):
        return '%r %r %r' % (self.vin, self.mmy, self.v_status)
    
    def __init__(self, vin, mmy, v_status):
        self.vin = vin
        self.mmy = mmy
        self.v_status = v_status

class Vehicle_insured(db.Model):
    __tablename__ = 'vehicle_insured'
    i_id = db.Column(db.Integer, db.ForeignKey('insurance_auto.i_id'), primary_key=True)
    vin = db.Column(db.String(17), db.ForeignKey('vehicle.vin'), primary_key=True)

    def __repr__(self):
        return '%r %r' % (self.i_id, self.vin)
    
    def __init__(self, i_id, vin):
        self.i_id = i_id
        self.vin = vin

class Drivers(db.Model):
    __tablename__ = 'drivers'
    license_number = db.Column(db.String(9), primary_key=True)
    fname = db.Column(db.String(30), nullable=False)
    lname = db.Column(db.String(30), nullable=False)
    birthday = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return '%r %r %r %r' % (self.license_number, self.fname, self.lname, self.birthday)
    
    def __init__(self, license_number, fname, lname, birthday):
        self.license_number = license_number
        self.fname = fname
        self.lname = lname
        self.birthday = birthday

class Vehicle_driver(db.Model):
    __tablename__ = 'vehicle_driver'
    license_number = db.Column(db.String(9), db.ForeignKey('drivers.license_number'), primary_key=True)
    vin = db.Column(db.String(17), db.ForeignKey('vehicle.vin'), primary_key=True)

    def __repr__(self):
        return '%r %r' % (self.license_number, self.vin)
    
    def __init__(self, license_number, vin):
        self.license_number = license_number
        self.vin = vin

if __name__ == '__main__':
    app.run(debug=True)