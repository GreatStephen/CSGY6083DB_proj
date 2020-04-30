from flask import Flask, render_template, Markup, request, session, url_for, redirect
from flask import make_response, flash
import time
app = Flask(__name__)

app.secret_key = 'hard to guess'

@app.route('/')
def index():
    if 'user' in session:
        return 'Hello %s!' % session['user']
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
            session['user'] = request.form['user']
            # flash('Login successfully!', 'message')
            # flash('Login as user: %s.' % request.form['user'], 'info')
            response = make_response('Admin login successfully!')
            response.set_cookie('login_time', time.strftime('%Y-%m-%d %H:%M:%S'))
            return redirect(url_for('index'))
        else:
            return 'No such user!'
    else:
        if 'user' in session:
            login_time = request.cookies.get('login_time')
            response = make_response('Hello %s, you logged in on %s' % (session['user'], login_time))
        else:
            title = request.args.get('title', 'Default')
            response = make_response(render_template('login.html', title=title), 200)
            response.headers['key'] = 'value'
            return response
    return response

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))    

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

if __name__ == '__main__':
    app.run(debug=True)