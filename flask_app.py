from flask import *
from functools import wraps
from flask_mail import Mail, Message
import sqlite3
import hashlib

DATABASE = '/home/NSYue/mysite/datastore.db'

app = Flask(__name__)
mail = Mail(app)
app.config.from_object('config')

app.secret_key = 'key'

item=['A4 lecture pad','7-colour sticky note with pen','A5 ring book','A5 note book with zip bag','2B pencil','Stainless steel tumbler','A4 clear holder','A4 vanguard file','Name card holder','Umbrella','School badge (Junior High)','School badge (Senior High)','Dunman dolls (pair)']
unitprice=[2.60,4.20,4.80,4.60,0.90,12.90,4.40,1.00,10.90,9.00,1.30,1.80,45.00]

def connect_db():
    return sqlite3.connect(app.config['DATABASE_PATH'])

def valid_signup(username, password, repassword, email):
    if (password!=repassword) or (len(password)>12) or (len(password)<4)  or (not '@' in email):
        return False
    else:
        for s in username:
            if not(s.isalpha() or s.isdigit()):
                return False
        for s in password:
            if not(s.isalpha() or s.isdigit()):
                return False
    return True

def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('log'))
    return wrap

@app.route('/')
def home():
    g.db  = connect_db()
    cur = g.db.execute('select id, item, unitprice from items')
    items = [dict(id=row[0], item=row[1], unitprice=row[2]) for row in cur.fetchall()]
    g.db.close()
    if 'logged_in' in session:
        return redirect(url_for('hello'))
    return render_template('home.html', items=items)

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    g.db = connect_db()
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']
        email = request.form['email']
       # password = hashlib.sha256(passoword).hexdigest()
        orderinfo = ''
        for i in range(0,13):
            if i!=12:
                orderinfo+="0."
            else:
                orderinfo+="0"
        if valid_signup(username,password,repassword,email):
            g.db.execute('INSERT INTO users VALUES (?,?,?,?)', [username,password,email,orderinfo])
            g.db.commit()
            g.db.close()
            return redirect(url_for('log'))
        else:
            error='Invalid username/password/email'
    return render_template('signup.html', error=error)

@app.route('/hello')
@login_required
def hello():
    g.db  = connect_db()
    cur = g.db.execute('select id, item, unitprice from items')
    items = [dict(id=row[0], item=row[1], unitprice=row[2]) for row in cur.fetchall()]
    g.db.close()
    return render_template('hello.html', items=items, logged_in = True)


@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('log'))

@app.route('/log', methods=['GET', 'POST'])
def log():
    g.db  = connect_db()
    cur = g.db.execute('SELECT * FROM users')
    total = cur.fetchall()
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
       # password = hashlib.sha256(passoword).hexdigest()
        if len(total) == 0:
            return redirect(url_for('signup'))
        else:
            for s in total:
                if not (s[0] == username) or not (s[1] == password):
                    error = 'Invalid Credentials. Please try again.'
                else:
                    session['logged_in'] = True
                    session['username'] = username
                    return redirect(url_for('hello'))
    return render_template('log.html', error=error)

@app.route('/order', methods=['POST', 'GET'])
@login_required
def order():
    g.db  = connect_db()
    cur = g.db.execute('select id, item, unitprice from items')
    items = [dict(id=row[0], item=row[1], unitprice=row[2]) for row in cur.fetchall()]
    error=''
    if 'username' in session:
        username=escape(session['username'])
        orderinfo=''
        if request.method == 'POST':
            number=[]
            for i in range(0,13):
                a  = request.form['number'+str(i+1)]
                if a.isdigit() and 100 > a >= 0:
                    number.append(a)
                    for i in range(0,13):
                        if number[i] == '':
                            number[i] = 0
                        if i!=12:
                            orderinfo+=str(number[i])+"."
                        else:
                            orderinfo+=str(number[i])
                    g.db.execute("UPDATE users SET orderinfo = '%s' WHERE username='%s'" % (orderinfo,username))
                    g.db.commit()
                    g.db.close()
                    return redirect(url_for('confirm'))
                else:
                    error = "Please enter an integer between 0 and 100 for the quantity of items."
    return render_template('order.html', items=items, error=error, logged_in = True)

@app.route('/confirm', methods=['POST', 'GET'])
def confirm():
    g.db  = connect_db()
    if 'username' in session:
        username=escape(session['username'])
        cur = g.db.execute("SELECT orderinfo FROM users WHERE username='%s'" % username)
        info = cur.fetchall()
        if info:
            orderinfo = str(info[0][0])
        else:
            orderinfo = ''
        orders=[]
        total=0
        listt=orderinfo.split('.')
        for i in range(0,13):
            if int(listt[i])!=0:
                order=[item[i], unitprice[i], int(listt[i])]
                total+=order[1]*order[2]
                orders.append(order)
    return render_template('confirm.html', total=total, orders=orders, logged_in = True)

@app.route('/delete')
@login_required
def delete():
    g.db = connect_db()
    if 'username' in session:
        username=escape(session['username'])
        orderinfo = ''
        for i in range(0,13):
            if i!=12:
                orderinfo+="0."
            else:
                orderinfo+="0"
        g.db.execute("UPDATE users SET orderinfo = '%s' WHERE username='%s'" % (orderinfo,username))
        g.db.commit()
        cur = g.db.execute("SELECT orderinfo FROM users WHERE username='%s'" % username)
        info = cur.fetchall()
        if info:
            orderinfo = str(info[0][0])
        else:
            orderinfo = ''
        orders=[]
        total=0
        listt=orderinfo.split('.')
        for i in range(0,13):
            if int(listt[i])!=0:
                order=[item[i], unitprice[i], int(listt[i])]
                total+=order[1]*order[2]
                orders.append(order)
        sign = "You have not taken any order yet!"
    return render_template('confirm.html',sign = sign, total=total, orders=orders, logged_in = True)

@app.route('/submit')
@login_required
def submit():
#    g.db  = connect_db()
#    if 'username' in session:
#        username=escape(session['username'])
#        cur = g.db.execute("SELECT orderinfo FROM users WHERE username='%s'" % username)
#        info = cur.fetchall()
#        curs = g.db.execute("SELECT email FROM users WHERE username='%s'" % username)
#        email = curs.fetchall()
#        if info:
#            orderinfo = str(info[0][0])
#        else:
#            orderinfo = ''
#        orders=[]
#        total=0
#        listt=orderinfo.split('.')
#        for i in range(0,13):
#            if int(listt[i])!=0:
#                order=[item[i], unitprice[i], int(listt[i])]
#                total+=order[1]*order[2]
#                orders.append(order)
#        with mail.connect() as conn:
#            message = 'Your order: %s Total price: %s.     If you have confirmed, please reply this email and come down to the DHS store during weekdays.' % (orders,total)
#            subject = "hello, %s" % username
#            msg = Message(recipients=[email, "nie.shuyue@dhs.sg"],
#                        sender= "nie.shuyue@dhs.sg",
#                        body=message,
#                        subject=subject)
#        conn.send(msg)
    return render_template('submit.html', logged_in = True)

if __name__ == '__main__':
    app.run(debug=True)