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
	admin = False
	if isAdmin():
		admin = True
		if not isValidOTP():
			return redirect(url_for('otp'))
	return render_template('index.html', admin=admin)

@app.route("/qrcode", methods=["GET"])
def get_qrcode():
    # please get /qrcode?data=<qrcode_data>
    data = request.args.get("data", "")
    return send_file(qrcode(data, mode="raw"), mimetype="image/png")

@app.route('/topup', methods=['GET','POST'])
def topup():
	if not isAdmin():
		return redirect(url_for('login'))
	if not isValidOTP():
		return redirect(url_for('otp'))
	code = None
	value = 0
	if request.method == 'POST':
		try:
			value = int(request.form['value'])
			if value <= 0:
				raise Exception('Less than zero')
			code = db.generateTopUp(value)
		except Exception as e:
			app.logger.critical(e)
	return render_template('topup.html', code=code, value=value, codes=[], totalvalue=db.getTopupBalance(), admin=True)

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
			try:
				if totp.verify(request.form['otp']):
					session['otp'] = True
					db.setOTPverified(session['username'])
					return redirect(url_for('index'))
			except Exception as e:
				app.logger.critical(e)
		if not db.isOTPverified(session['username']):
			secret = db.getOTPSecret(session['username'])
			code = pyotp.totp.TOTP(secret).provisioning_uri(name=session['username'], issuer_name=domain)
			return render_template('generateOTP.html', url=code, code=urllib.parse.quote_plus(code), error=(request.method == 'POST'), admin=True)
		return render_template('generateOTP.html', error=(request.method == 'POST'), admin=True)
	return redirect(url_for('login'))

def isValidOTP():
	return 'otp' in session

def isAdmin():
	if 'username' in session:
		if db.isAdmin(session['username']):
			return True
	return False

@app.route('/login', methods=['GET','POST'])
def login():
	if isAdmin():
		if not isValidOTP():
			return redirect(url_for('otp'))
		return redirect(url_for('index'))
	if request.method == 'POST':
		try:
			if db.checkAdmin(request.form['username'], request.form['password']):
				session['username'] = request.form['username']
				print('Username:' + request.form['username'])
				app.logger.critical(session)
				return redirect(url_for('otp'))
			else:
				app.logger.critical("Failed to check")
		except Exception as e:
			app.logger.critical(e)
		return render_template('login.html', error=True)
	return render_template('login.html', error=False)

@app.route('/logout')
def logout():
	session.pop('username',None)
	session.pop('otp',None)
	return redirect(url_for('index'))

@app.route('/cards')
def page_cards():
	if not isAdmin():
		return redirect(url_for('login'))
	if not isValidOTP():
		return redirect(url_for('otp'))
	value = db.getBalance()
	cards = db.getCards()
	return render_template('cards.html', totalvalue=value, cards=cards, admin=True)

@app.route('/products', methods=['GET','POST'])
def page_products():
	if request.method == 'POST':
		if not isAdmin():
			return redirect(url_for('login'))
		if not isValidOTP():
			return redirect(url_for('otp'))
		if 'restock' in request.form:
			try:
				db.changeProductStock(request.form['ean'], request.form['restock'])
			except Exception as e:
				app.logger.critical(e)
		elif 'name' in request.form:
			try:
				db.addProduct(request.form['ean'], request.form['name'], request.form['price'], request.form['stock'])
			except Exception as e:
				app.logger.critical(e)
	products = db.getProducts()
	return render_template('products.html', products=products, admin=isAdmin())
