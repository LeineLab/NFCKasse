from flask import Flask, render_template, request, send_file, session, escape, url_for, redirect
from flask_qrcode import QRcode
import uuid
import pyotp
import socket
import urllib.parse
import settings

app = Flask(__name__,
	static_url_path='')
qrcode = QRcode(app)
db = None

app.secret_key = uuid.uuid4().hex

try:
	domain = settings.domain
except AttributeError:
	domain = socket.gethostname()

@app.route("/")
def index():
	return "<p>Hello, World!</p>"

@app.route("/qrcode", methods=["GET"])
def get_qrcode():
    # please get /qrcode?data=<qrcode_data>
    data = request.args.get("data", "")
    return send_file(qrcode(data, mode="raw"), mimetype="image/png")

@app.route('/topup')
def topup():
	value = 5
	code = db.generateTopUp(value)
	print(code)
	return f'<img src="/qrcode?data=' + code + '">'

@app.route('/otp', methods=['GET','POST'])
def otp():
	if isAdmin():
		if not db.hasOTPSecret(session['username']):
			secret = pyotp.random_base32()
			db.setOTPSecret(session['username'], secret)
		secret = db.getOTPSecret(session['username'])
		if 'otp' in session:
			return redirect(url_for('index'))
		if request.method == 'POST':
			totp = pyotp.TOTP(secret)
			if totp.verify(request.form['otp']):
				session['otp'] = True
				db.setOTPverified(session['username'])
				return redirect(url_for('index'))
		if not db.isOTPverified(session['username']):
			secret = db.getOTPSecret(session['username'])
			code = pyotp.totp.TOTP(secret).provisioning_uri(name=session['username'], issuer_name=domain)
			return render_template('generateOTP.html', url=code, code=urllib.parse.quote_plus(code), error=(request.method == 'POST'))
		return render_template('generateOTP.html', error=(request.method == 'POST'))
	return redirect(url_for('login'))

def isValidOTP():
	return 'otp' in session

def isAdmin():
	if 'username' in session:
		if db.checkAdmin(session['username']):
			return True
	return False

@app.route('/login', methods=['GET','POST'])
def login():
	if request.method == 'POST':
		session['username'] = 'sndstrm'
		return redirect(url_for('otp'))
	return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('username',None)
	return redirect(url_for('index'))

@app.route('/cards')
def page_cards():
	if isAdmin():
		value = db.getBalance()
		cards = db.getCards()
		return render_template('cards.html', totalvalue=value, cards=cards)
	return redirect(url_for('login'))

@app.route('/products')
def page_products():
	products = db.getProducts()
	return render_template('products.html', products=products)
