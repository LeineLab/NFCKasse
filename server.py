from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, Response, render_template, request, send_file, session, url_for, redirect, make_response
from markupsafe import escape
from flask_qrcode import QRcode
from authlib.integrations.flask_client import OAuth
import datetime
import uuid
import pyotp
import socket
import urllib.parse
import settings


app = Flask(__name__,
	static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
qrcode = QRcode(app)
db = None

try:
	app.secret_key = settings.server_secret
except AttributeError:
	app.secret_key = uuid.uuid4().hex

try:
	domain = settings.domain
except AttributeError:
	domain = socket.gethostname()

try:
	oauth = OAuth(app)
	oauth.register(
		client_id=settings.openid_id,
		client_secret=settings.openid_secret,
		id_token_signing_alg_values_supported=["HS256", "RS256"],
		name='openid',
		server_metadata_url=settings.openid_url,
		client_kwargs={
			'scope': 'openid email profile'
		}
	)
except AttributeError:
	oauth = None

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
    return send_file(qrcode(data, mode="raw", border=1), mimetype="image/png")

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
			value = float(request.form['value'])
			if value <= 0:
				raise Exception('Less than zero')
			code = db.generateTopUp(value, session['username'])
		except Exception as e:
			app.logger.critical(e)
	return render_template('topup.html', code=code, value=value, codes=[], totalvalue=db.getTopupBalance(), admin=True)

@app.route('/history/transactions', methods=['POST'])
def getHistoryTransactions():
	if not isAdmin():
		return redirect(url_for('login'))
	if not isValidOTP():
		return redirect(url_for('otp'))
	from_date = request.form['from_date']
	to_date = request.form['to_date']
	if to_date is None or to_date == '':
		to_date = '%s' % (datetime.datetime.today().date(), )

	transactions = db.getHistoryTransactions(from_date, to_date)
	csv = '"Date","Value","EAN","Product"'
	for transaction in transactions:
		csv += '\n"%s",%.2f,"%s","%s"' % (transaction['tdate'], transaction['value'], transaction['ean'], transaction['name'])
	return Response(
		csv,
		mimetype="text/csv",
		headers={"Content-disposition":
				"attachment; filename=transactions_%s_%s.csv" % (from_date, to_date)
		}
	)

@app.route('/history/topups', methods=['POST'])
def getHistoryTopup():
	if not isAdmin():
		return redirect(url_for('login'))
	if not isValidOTP():
		return redirect(url_for('otp'))
	from_date = request.form['from_date']
	to_date = request.form['to_date']
	if to_date is None or to_date == '':
		to_date = '%s' % (datetime.datetime.today().date(), )
	transactions = db.getHistoryTopups(from_date, to_date)
	csv = '"Date","Value"'
	for transaction in transactions:
		csv += '\n"%s",%.2f' % (transaction['tdate'], transaction['value'])
	return Response(
		csv,
		mimetype="text/csv",
		headers={"Content-disposition":
				"attachment; filename=topups_%s_%s.csv" % (from_date, to_date)
		}
	)

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
	if not settings.force_otp and not db.hasOTPSecret(session['username']):
		return True
	return 'otp' in session or 'oauth' in session

def isAdmin():
	if 'username' in session:
		if db.isAdmin(session['username']):
			return True
	session.clear()
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
		return render_template('login.html', error=True, oauth=(oauth is not None))
	return render_template('login.html', error=False, oauth=(oauth is not None))

@app.route('/oauthlogin')
def oauthlogin():
	if oauth is None:
		return redirect(url_for('login'))
	redirect_uri = url_for('auth', _external=True)
	return oauth.openid.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
	try:
		token = oauth.openid.authorize_access_token()
		session['username'] = token['userinfo']['preferred_username']
		session['oauth'] = True
		# Add potential new admin
		if not db.isAdmin(session['username']):
			app.logger.critical('Creating new admin for OpenID user')
			db.addAdmin(session['username'], None)
		return redirect('/')
	except:
		app.logger.exception('OpenID Login failed')
		return redirect(url_for('login'))

@app.route('/logout')
def logout():
	session.pop('username',None)
	session.pop('otp',None)
	session.pop('oauth',None)
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

@app.route('/export')
def page_export():
	if not isAdmin():
		return redirect(url_for('login'))
	elif not isValidOTP():
		return redirect(url_for('otp'))
	return render_template('export.html', admin=True)

@app.route('/products', methods=['GET','POST'])
def page_products():
	if request.method == 'POST':
		if not isAdmin():
			return redirect(url_for('login'))
		elif not isValidOTP():
			return redirect(url_for('otp'))
		elif 'restock' in request.form:
			try:
				db.changeProductStock(request.form['ean'], request.form['restock'], session['username'])
				db.changeProductPrice(request.form['ean'], request.form['price'], session['username'])
				db.changeProductCategory(request.form['ean'], request.form['category'], session['username'])
			except Exception as e:
				app.logger.critical(e)
		elif 'name' in request.form:
			try:
				db.addProduct(request.form['ean'], request.form['name'], request.form['price'], request.form.get('stock', 0), request.form.get('category'), session['username'])
			except Exception as e:
				app.logger.critical(e)
	products = db.getProducts()
	categories = db.getProductCategories()
	sales_7d = db.getProductMaxSales(7)
	sales_30d = db.getProductMaxSales(30)
	revenue_7d = db.getRevenue(7)
	revenue_30d = db.getRevenue(30)
	return render_template('products.html',
		products=products,
		categories=categories,
		sales_7d=sales_7d,
		sales_30d=sales_30d,
		revenue_7d=revenue_7d,
		revenue_30d=revenue_30d,
		admin=isAdmin()
	)

@app.route('/products.json', methods=['GET'])
def page_product_json():
	products = db.getProducts()
	resp = make_response(render_template('products.json',
		products=products,
		category=request.args.get('category', None)
	))
	resp.headers['Content-Type'] = "text/json; charset=utf-8"
	return resp

@app.route('/product_alias', methods=['GET','POST'])
def page_product_alias():
	if request.method == 'POST':
		if not isAdmin():
			return redirect(url_for('login'))
		elif not isValidOTP():
			return redirect(url_for('otp'))
		elif 'target' in request.form:
			try:
				db.addProductAlias(request.form['ean'], request.form['target'], session['username'])
			except Exception as e:
				app.logger.critical(e)
	products = db.getProducts()
	product_alias = db.getProductAlias()
	return render_template('product_alias.html',
		products=products,
		product_alias=product_alias,
		admin=isAdmin()
	)

@app.route('/product_categories', methods=['GET','POST'])
def page_product_categories():
	if request.method == 'POST':
		if not isAdmin():
			return redirect(url_for('login'))
		elif not isValidOTP():
			return redirect(url_for('otp'))
		elif 'name' in request.form:
			try:
				db.addProductCategory(request.form['name'], session['username'])
			except Exception as e:
				app.logger.critical(e)
	categories = db.getProductCategories()
	return render_template('product_categories.html',
		categories=categories,
		admin=isAdmin()
	)

@app.route('/admin', methods=['GET','POST'])
def page_admin():
	if not isAdmin():
		return redirect(url_for('login'))
	if not isValidOTP():
		return redirect(url_for('otp'))
	error = False
	if request.method == 'POST':
		if 'add' in request.form:
			if request.form['password'] != request.form['password2']:
				error = "Passwörter stimmen nicht überein"
			else:
				if not db.addAdmin(request.form['username'], request.form['password']):
					error = "Konnte Benutzer nicht anlegen"
		elif 'password' in request.form and 'password2' in request.form:
			if request.form['password'] != request.form['password2']:
				error = "Passwörter stimmen nicht überein"
			else:
				if not db.changePassword(session['username'], request.form['password']):
					error = "Konnte Passwort nicht ändern"
		elif 'deactivate' in request.form:
			try:
				if request.form['username'] != session['username']:
					db.deactivateAdmin(request.form['username'], session['username'])
			except Exception as e:
				app.logger.critical(e)
		elif 'reactivate' in request.form:
			try:
				if request.form['username'] != session['username']:
					db.reactivateAdmin(request.form['username'], session['username'])
			except Exception as e:
				app.logger.critical(e)
		elif 'reset' in request.form:
			try:
				if request.form['username'] != session['username']:
					db.resetOTP(request.form['username'], session['username'])
			except Exception as e:
				app.logger.critical(e)
	admins = db.getAdmins()
	return render_template('admins.html', username=session['username'], admins=admins, error=error, admin=True)
