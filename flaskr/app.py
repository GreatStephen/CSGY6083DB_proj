from flask import Flask, render_template, Markup, request, session, url_for, redirect
from flask import make_response, flash
from flask_sqlalchemy import SQLAlchemy
import time

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess'
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:root@localhost:3306/mysql_test'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True

db = SQLAlchemy(app)

# app.secret_key = 'hard to guess'

@app.route('/')
def index():
    username = request.cookies.get('myname')
    if username in session:
        return 'Hello %s!' % username
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
        if request.form['user'] == 'admin':
            session[request.form['user']] = 'online'
            # flash('Login successfully!', 'message')
            # flash('Login as user: %s.' % request.form['user'], 'info')
            response = make_response(redirect(url_for('index')))
            response.set_cookie('login_time', time.strftime('%m-%d-%Y %H:%M:%S'))
            response.set_cookie('myname', request.form['user'])
            return response
        else:
            return 'No such user! Please register.'

    else: # GET
        username = request.cookies.get('myname')
        if username in session:
            login_time = request.cookies.get('login_time')
            response = make_response('Hello %s, you logged in on %s' % (session['user'], login_time))
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
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')
        # TODO: MD5 encription on password

        new_user = User(None, new_username, new_password)
        db.session.add(new_user)
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


class User(db.Model):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '%r %r %r'%(self.id, self.username, self.password)
    
    def __init__(self, iden, un, pd):
        self.id = iden
        self.username=un
        self.password=pd


if __name__ == '__main__':
    app.run(debug=True)