import re
from flask import Flask,render_template,request,url_for,session,redirect
from flask_mysqldb import MySQL
import MySQLdb.cursors
from mapbox import Maps,Geocoder, StaticStyle
from mapbox.services.base import Service
from mapbox.services.static import Static
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_mysqldb import MySQL
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import csv
from datetime import datetime

app=Flask(__name__)

app.secret_key="password"

mysql=MySQL(app)
app.config["MYSQL_HOST"]="127.0.0.1"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]="password"
app.config["MYSQL_DB"]="project"



@app.route('/')
def home():
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('index.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/admin')
def adminhome():
    if 'loggedin2' in session:
        # User is loggedin show them the home page
        return render_template('admin.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('admin_login'))


@app.route('/register', methods=['POST','GET'])
def register():
    print("akashregister")
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL,%s, %s, %s,NULL)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query="SELECT * FROM accounts WHERE username = %s AND password = %s AND adm = null"
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            print("no user '%s' ",username)
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)



@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username1 = request.form['username']
        password1 = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username = %s AND password = %s AND adm = 'yes'", (username1, password1))
        print(username1,password1)
        account2 = cursor.fetchone()
        print(account2)
        if account2:
            session['loggedin2'] = True
            session['id'] = account2['id']
            session['username'] = account2['username']
            return redirect(url_for('adminhome'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('admin_login.html', msg=msg)


@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return redirect(url_for('login'))

#service notification
def notify():
    date = datetime.today().strftime('%Y-%m-%d')
    f = open(r"rahulproj\bought_cars.csv",'r', newline='')
    csv_r = csv.reader(f)
    for rec in csv_r:
        if rec[0] == 'Car_ID':
            continue
        if rec[2] >= date:
            notif = Mail(from_email='rahulsiv2108@gmail.com',
                         to_emails=rec[3],
                         subject='Time to take your car to the service centre',
                         html_content= "<p>Hi! It's been 6 months since you have had your car checked. Ensure that you take your car to the nearest showroom for better performance! Happy driving!</p>"
                        )
            sg_key = "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"
            try:
                mail = SendGridAPIClient(sg_key)
                mail.send(notif)
            except Exception as e:
                print(e)
    f.close()

#home route
@app.route('/buyers', methods = ['GET', 'POST'])
def buyer():
    notify()
    if request.method == 'POST':
        car = request.form
        carType = car['search']
        cursor = mysql.connection.cursor()
        cursor.execute('select car_id, name from buyer where type= % s;', (carType,))
        data = cursor.fetchall()
        return render_template('buyer.html', data=data)
    cursor = mysql.connection.cursor()
    cursor.execute('select car_id, name from buyer;')
    data = cursor.fetchall()
    return render_template('buyer.html', data=data)

#more info route
@app.route('/buyers/more')
def info():
    file = open('info.txt', 'r')
    text = file.readlines()
    file.close()
    return render_template('info.html', text=text)

#car route
@app.route('/buyers/<car_id>')
def car(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from buyer where car_id= % s;', (car_id,))
    info = cursor.fetchall()
    return render_template('car.html', info=info)

#automated e-mail route
@app.route('/buyers/<car_id>/mail')
def send(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select seller_email from buyer where car_id= % s;', (car_id))
    data = cursor.fetchone()
    msg = Mail(
        from_email='rahulsiv2108@gmail.com',
        to_emails='sidsiv2007@gmail.com',
        subject='Seller contact info',
        html_content=f'<div>Seller contact info has been sent!</div><p>{data}</p>')
    sg_key = "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"
    try:
        sg = SendGridAPIClient(sg_key)
        res = sg.send(msg)
    except Exception as e:
        print(e)
    return redirect(f'/{car_id}')

#test drive route
@app.route('/buyers/test-drive', methods= ['GET', 'POST']) 
def test_drive():
    cursor = mysql.connection.cursor()
    cur_date = datetime.today().strftime('%Y-%m-%d')
    cur_date_str = cur_date.replace('-', '')
    cursor.execute('select slot,car_id from testdrive')
    slots = cursor.fetchall()
    for i in slots:
        slot_date = str(i[0]).replace('-', '')
        if int(slot_date) < int(cur_date_str):
            cursor.execute('''update testdrive set slot = curdate() where car_id = % s;''', (i[1],))
            mysql.connection.commit()
    if request.method == 'POST':
        form = request.form
        name = form['name']
        cursor.execute('select * from testdrive where name = % s;', (name,))
        elements = cursor.fetchall()
        return render_template('test_drive.html', elements=elements)
    cursor.execute('select * from testdrive;')
    elements = cursor.fetchall()
    return render_template('test_drive.html', elements=elements)

#test drive this car route
@app.route('/buyers/test-drive/<car_id>')
def td_car(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from testdrive t, buyer b where t.Car_ID = % s and t.Car_ID = b.Car_ID;', (car_id,))
    slot_data = cursor.fetchall()
    return render_template('tdcar.html', slot_data=slot_data)

#test drive confirmation
@app.route('/buyers/test-drive/<car_id>/book')
def confirm(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select seller_email from buyer where Car_ID = % s;', (car_id,))
    email = cursor.fetchone()
    td_update = Mail(from_email='rahulsiv2108@gmail.com',
                     to_emails=email[0],
                     subject= 'Test drive slot update',
                     html_content= '<p>A prospective buyer has booked a slot to test drive your car.</p>'
                    )
    sg_key = "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"
    try:
        sg = SendGridAPIClient(sg_key)
        sg.send(td_update)
    except Exception as e:
        print(e)
    return redirect(f'/test-drive/{car_id}')


if __name__=="__main__":
    app.run(debug=True)