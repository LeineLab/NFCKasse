#!/opt/kasse/venv/bin/python3

import mysql.connector
import uuid
import bcrypt

class Database:
	def __init__(self, **kwargs):
		self.db_host = kwargs['host']
		self.db_user = kwargs['user']
		self.db_password = kwargs['password']
		self.db_database = kwargs['database']
		self.db = None
		self.connect()

	def connect(self):
		if self.db is not None and self.db.is_connected():
			try:
				self.db.ping(True)
				return True
			except mysql.connector.errors.InterfaceError:
				pass
		try:
			self.db = mysql.connector.connect(
				host = self.db_host,
				user = self.db_user,
				password = self.db_password,
				database = self.db_database
			)
			#self.db.autocommit = True
			self.cursor = self.db.cursor(dictionary=True)
			self.cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
			return True
		except Exception as e:
			return False

	def ping(self):
		if self.db is None:
			return self.connect()
		try:
			self.db.ping(True)
			return True
		except mysql.connector.errors.InterfaceError:
			return False

	"""Web frontend check, if user exists
	"""
	def isAdmin(self, name):
		if not self.connect():
			return False
		self.cursor.execute('SELECT username FROM admins WHERE username = %s', (name, ))
		try:
			result = self.cursor.fetchone()
			if result is None:
				return False
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, validate password
	"""
	def checkAdmin(self, name, password):
		if not self.connect():
			return False
		self.cursor.execute('SELECT password FROM admins WHERE username = %s AND active = 1', (name, ))
		try:
			result = self.cursor.fetchone()
			return bcrypt.checkpw(password.encode('utf-8'), result['password'].encode('utf-8'))
		except mysql.connector.Error as error:
			return False

	"""Web frontend, add new user
	"""
	def addAdmin(self, name, password):
		if not self.connect():
			return False
		try:
			hash = None
			if password is not None:
				salt = bcrypt.gensalt()
				hash = bcrypt.hashpw(password.encode('utf-8'), salt)
			self.cursor.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', (name, hash))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, deactivate user
	"""
	def deactivateAdmin(self, name, current_user):
		if not self.connect():
			return False
		try:
			self.cursor.execute('UPDATE admins SET active = 0 WHERE username=%s', (name, ))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "Useraccount %s reactivated")', (current_user, name))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, reactivate user
	"""
	def reactivateAdmin(self, name, current_user):
		if not self.connect():
			return False
		try:
			self.cursor.execute('UPDATE admins SET active = 1 WHERE username=%s', (name, ))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "Useraccount %s reactivated")', (current_user, name))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, change password of user
	"""
	def changePassword(self, name, password):
		if not self.connect():
			return False
		try:
			salt = bcrypt.gensalt()
			hash = bcrypt.hashpw(password.encode('utf-8'), salt)
			self.cursor.execute('UPDATE admins SET password=%s WHERE username=%s', (hash, name))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "Password changed")', (name,))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, list users
	"""
	def getAdmins(self):
		if not self.connect():
			return []
		self.cursor.execute('SELECT username, otp_validated as otp, active FROM admins')
		try:
			results = self.cursor.fetchall()
			return results
		except mysql.connector.Error as error:
			return []

	"""Web frontend, reset OTP for user

	User needs to login after the reset and complete the OTP setup
	"""
	def resetOTP(self, name, current_user):
		if not self.connect():
			return False
		try:
			self.cursor.execute('UPDATE admins SET otps=NULL, otp_validated=0 WHERE username = %s', (name, ))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "OTP reset for user %s")', (current_user, name))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, get OTP secret for user
	"""
	def getOTPSecret(self, name):
		if not self.connect():
			return None
		self.cursor.execute('SELECT otps FROM admins WHERE username = %s', (name, ))
		try:
			result = self.cursor.fetchone()
			return result['otps']
		except mysql.connector.Error as error:
			return None
		except TypeError as error:
			return None

	"""Web frontend, check if user already setup OTP
	"""
	def hasOTPSecret(self, name):
		return self.getOTPSecret(name) is not None

	"""Web frontend, setup OTP secret for user
	"""
	def setOTPSecret(self, name, secret):
		if not self.connect():
			return False
		try:
			self.cursor.execute('UPDATE admins SET otps = %s WHERE username = %s', (secret, name))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "OTP set")', (name,))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, check if user has validated the OTP secret
	"""
	def isOTPverified(self, name):
		if not self.connect():
			return 0
		self.cursor.execute('SELECT otp_validated FROM admins WHERE username = %s', (name, ))
		try:
			result = self.cursor.fetchone()
			return result['otp_validated']
		except mysql.connector.Error as error:
			return 0
		except TypeError as error:
			return 0

	"""Web frontend, set OTP secret as validated for user
	"""
	def setOTPverified(self, name):
		if not self.connect():
			return False
		try:
			self.cursor.execute('UPDATE admins SET otp_validated = 1 WHERE username = %s', (name,))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "OTP verified")', (name,))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Get referenced EAN for alias EAN

	@returns EAN
	"""
	def getAlias(self, ean):
		if not self.connect():
			return ean
		self.cursor.execute('SELECT target FROM product_alias WHERE ean = %s', (ean, ))
		try:
			result = self.cursor.fetchone()
			return result['target']
		except TypeError:
			return ean
		except mysql.connector.Error as error:
			return ean

	"""Get product for EAN

	@returns Tuple of (name, price)
	"""
	def getProduct(self, ean):
		if not self.connect():
			return (None, None)
		self.cursor.execute('SELECT ean, name, price, stock FROM products WHERE ean = %s', (ean, ))
		try:
			result = self.cursor.fetchone()
			return result
		except TypeError:
			return {"ean": ean, "name": None, "price": None, "stock": None}
		except mysql.connector.Error as error:
			return {"ean": ean, "name": None, "price": None, "stock": None}

	"""Get product category for EAN

	@returns category if present
	"""
	def getProductCategory(self, ean):
		if not self.connect():
			return None
		self.cursor.execute('SELECT category FROM products WHERE ean = %s', (ean, ))
		try:
			result = self.cursor.fetchone()
			return result['category']
		except TypeError:
			return None
		except mysql.connector.Error as error:
			return None

	"""Web frontend, get list of aliased products
	"""
	def getProductAlias(self):
		if not self.connect():
			return []
		self.cursor.execute('SELECT a.ean, a.target, p.name FROM product_alias a LEFT JOIN products p ON a.target = p.ean')
		try:
			results = self.cursor.fetchall()
			return results
		except TypeError:
			return []
		except mysql.connector.Error as error:
			return []

	"""Web frontend, get list of product categoriess
	"""
	def getProductCategories(self):
		if not self.connect():
			return []
		self.cursor.execute('SELECT name FROM product_categories ORDER BY name ASC')
		try:
			results = self.cursor.fetchall()
			return results
		except TypeError:
			return []
		except mysql.connector.Error as error:
			return []

	"""Web frontend, get list of products
	"""
	def getProducts(self):
		if not self.connect():
			return []
		self.cursor.execute('SELECT p.ean, p.name, p.price, p.stock, p.category, IFNULL(t1.sales_7d, 0) as sales_7d, IFNULL(t2.sales_30d, 0) as sales_30d FROM products p LEFT JOIN (SELECT count(tid) AS sales_7d, ean FROM transactions WHERE ean IS NOT NULL AND tdate >= DATE_SUB(now(), INTERVAL 7 DAY) GROUP BY ean) t1 ON p.ean = t1.ean LEFT JOIN (SELECT count(tid) AS sales_30d, ean FROM transactions WHERE ean IS NOT NULL AND tdate >= DATE_SUB(now(), INTERVAL 30 DAY) GROUP BY ean) t2 ON p.ean = t2.ean')
		try:
			results = self.cursor.fetchall()
			return results
		except TypeError:
			return []
		except mysql.connector.Error as error:
			return []

	"""Web frontend, get maximum sales in last n days

	@param duration Duration to get sales for in days
	"""
	def getProductMaxSales(self, duration):
		if not self.connect():
			return None
		self.cursor.execute('SELECT IFNULL(MAX(s.sales), 1) as max_sales FROM (SELECT count(tid) AS sales, ean FROM transactions WHERE ean IS NOT NULL AND tdate >= DATE_SUB(now(), INTERVAL %s DAY) GROUP BY ean) s', (duration, ))
		try:
			result = self.cursor.fetchone()
			return result['max_sales']
		except TypeError:
			return None
		except mysql.connector.Error as error:
			return None

	"""Web frontend, get overall revenue in last n days

	@param duration Duration to get revenue for in days
	"""
	def getRevenue(self, duration):
		if not self.connect():
			return None
		self.cursor.execute('SELECT SUM(r.revenue) as overall_revenue FROM (SELECT count(tid) * p.price AS revenue FROM transactions t JOIN products p ON t.ean = p.ean WHERE t.ean IS NOT NULL AND t.tdate >= DATE_SUB(now(), INTERVAL %s DAY) GROUP BY t.ean) r', (duration, ))
		try:
			result = self.cursor.fetchone()
			return result['overall_revenue']
		except TypeError:
			return None
		except mysql.connector.Error as error:
			return None

	"""Register new card
	"""
	def addCard(self, hash):
		if not self.connect():
			return False
		try:
			self.cursor.execute('INSERT INTO cards (uid) VALUES (%s)', (hash, ))
			result = self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Check if card is registered and return value
	"""
	def getCard(self, hash):
		if not self.connect():
			return None
		try:
			self.cursor.execute('SELECT value FROM cards WHERE uid = %s', (hash, ))
			result = self.cursor.fetchone()
			return result['value']
		except mysql.connector.Error as error:
			return None
		except TypeError:
			return None

	"""Web frontend, list all cards and values
	"""
	def getCards(self):
		if not self.connect():
			return []
		try:
			self.cursor.execute('SELECT uid, value FROM cards')
			results = self.cursor.fetchall()
			return results
		except mysql.connector.Error as error:
			return []
		return []

	"""Web frontend, get transaction history
	"""
	def getHistoryTransactions(self, from_date, to_date):
		if not self.connect():
			return []
		try:
			self.cursor.execute('SELECT t.ean, p.name, t.value, t.tdate FROM transactions t JOIN products p ON t.ean = p.ean WHERE tdate >= %s AND tdate <= %s ORDER BY tdate ASC', (from_date, to_date))
			results = self.cursor.fetchall()
			return results
		except mysql.connector.Error as error:
			return []

	"""Web frontend, get topup history
	"""
	def getHistoryTopups(self, from_date, to_date):
		if not self.connect():
			return []
		try:
			self.cursor.execute('SELECT tdate, value FROM transactions WHERE tdate >= %s AND tdate <= %s AND ean IS NULL AND exchange_with_uid IS NULL ORDER BY tdate ASC', (from_date, to_date))
			results = self.cursor.fetchall()
			return results
		except mysql.connector.Error as error:
			return []

	"""Web frontend, get total credits of all cards
	"""
	def getBalance(self):
		if not self.connect():
			return float('nan')
		try:
			self.cursor.execute('SELECT COALESCE(SUM(value),0) as totalvalue FROM cards')
			result = self.cursor.fetchone()
			return result['totalvalue']
		except mysql.connector.Error as error:
			return float('nan')
		return float('nan')

	"""Web frontend, get total topup value not redeemed
	"""
	def getTopupBalance(self):
		if not self.connect():
			return 0
		try:
			self.cursor.execute('SELECT COALESCE(SUM(value),0) as totalvalue FROM topups WHERE used=0')
			result = self.cursor.fetchone()
			return result['totalvalue']
		except mysql.connector.Error as error:
			return 0
		return 0

	"""Web frontend, generate topup hash for a given amount
	"""
	def generateTopUp(self, amount, username):
		if not self.connect():
			return None
		try:
			code = uuid.uuid4().hex
			print(code)
			self.cursor.execute('INSERT INTO topups (code, value, created_on, created_by) VALUES (%s, %s, NOW(), %s)', (code, amount, username))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "Topupcode %s generated")', (current_user, code))
			self.db.commit()
			return code
		except TypeError:
			return None

	"""Check if topup code is existing

	@return Tuple of (value, used)
	"""
	def checkTopUp(self, code):
		if not self.connect():
			return None, None
		try:
			self.cursor.execute('SELECT value, used FROM topups WHERE code = %s', (code, ))
			result = self.cursor.fetchone()
			return result['value'], result['used']
		except TypeError:
			return None, None

	"""Redeem topup code for card
	"""
	def topUpCard(self, cardhash, code):
		if not self.connect():
			return False
		try:
			value, used = self.checkTopUp(code)
			code = code.decode('utf-8')
			if used == 0:
				self.cursor.execute('UPDATE topups SET used = 1, used_on = NOW(), used_by = %s WHERE code = %s', (cardhash, code))
				self.cursor.execute('UPDATE cards SET value = value + (%s) WHERE uid = %s', (float(value), cardhash))
				self.cursor.execute('INSERT INTO transactions (uid, topupcode, value, tdate) VALUES (%s, %s, %s, NOW())', (cardhash, code, value))
				try:
					self.cursor.execute('INSERT INTO sessions (uid, machine, start_time, end_time, price) VALUES (%s, \'topup\', UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), %s)', (cardhash, value))
				except Exception as e: #no laser
					print(e)
					pass
				self.db.commit()
				return True
		except mysql.connector.Error as error:
			print(error)
			#logger.exception("Topup")
			self.db.rollback()
		return False

	"""Deduct or increase value of card

	@return true if increase or deduction is valid, false if value below 0 afterwards or unsuccessful
	"""
	def changeCardValue(self, hash, value):
		if not self.connect():
			return False
		v = self.getCard(hash)
		if v is None:
			return False
		if -value > v:
			return False
		try:
			self.cursor.execute('UPDATE cards SET value = value + (%s) WHERE uid = %s', (value, hash))
			self.db.commit()
		except mysql.connector.Error as error:
			self.db.rollback()
			return False
		return self.cursor.rowcount != 0

	"""Web frontend, increase or reduce product stock
	"""
	def changeProductStock(self, ean, amount, current_user):
		if not self.connect():
			return False
		if amount is None or amount == 0:
			return True
		try:
			self.cursor.execute('UPDATE products SET stock = stock + (%s) WHERE ean = %s', (amount, ean))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "Changed stock of product %s by %s")', (current_user, ean, int(amount)))
			self.db.commit()
			return self.cursor.rowcount != 0
		except mysql.connector.errors.DataError:
			return False

	"""Web frontend, change product price
	"""
	def changeProductPrice(self, ean, price, current_user):
		if not self.connect():
			return False
		product = self.getProduct(ean)
		if float(product['price']) == float(price):
			return True
		try:
			self.cursor.execute('UPDATE products SET price = (%s) WHERE ean = %s', (price, ean))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "Changed price of product %s from %s to %s")', (current_user, ean, product['price'], float(price)))
			self.db.commit()
			return self.cursor.rowcount != 0
		except mysql.connector.errors.DataError:
			return False

	"""Web frontend, change product category
	"""
	def changeProductCategory(self, ean, category, current_user):
		if not self.connect():
			return False
		old_category = self.getProductCategory(ean)
		if old_category == category:
			return True
		try:
			self.cursor.execute('UPDATE products SET category = (%s) WHERE ean = %s', (category, ean))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "Changed category of product %s from %s to %s")', (current_user, ean, old_category, category))
			self.db.commit()
			return self.cursor.rowcount != 0
		except mysql.connector.errors.DataError:
			return False

	"""Buy a product, deduct stock and card value, create transaction
	"""
	def buyProduct(self, cardhash, ean):
		if not self.connect():
			return False
		try:
			self.cursor.execute('SELECT name, price FROM products WHERE ean = %s', (ean, ))
			result = self.cursor.fetchone()
			name = result['name']
			price = result['price']
			#should fail if result is < 0, as value is unsigned
			self.cursor.execute('UPDATE cards SET value = value - %s WHERE uid = %s', (price, cardhash))
			self.cursor.execute('UPDATE products SET stock = stock - 1 WHERE ean = %s', (ean, ))
			self.cursor.execute('INSERT INTO transactions (uid, ean, value, tdate) VALUES (%s, %s, %s, NOW())', (cardhash, ean, -price))
			try:
				self.cursor.execute('INSERT INTO sessions (uid, machine, comment, start_time, end_time, price) VALUES (%s, \'material\', %s, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), %s)', (cardhash, name, -price))
			except Exception as e: #no laser
				print(e)
				pass
			self.db.commit()
			return True
		except mysql.connector.errors.DataError:
			self.db.rollback()
		return False

	"""Web frontend, add new product category
	"""
	def addProductCategory(self, name, current_user):
		if not self.connect():
			return False
		try:
			self.cursor.execute('INSERT INTO product_categories (name) VALUES (%s)', (name, ))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "New category: %s")', (current_user, name))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			print(error)
			return False

	"""Web frontend, add new product
	"""
	def addProduct(self, ean, name, price, stock, category, current_user):
		if not self.connect():
			return False
		try:
			self.cursor.execute('INSERT INTO products (ean, name, price, stock, category) VALUES (%s, %s, %s, %s, %s)', (ean, name, price, stock, category))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "New product: %s, %s for %s in %s. Initial stock: %s")', (current_user, ean, name, price, category, stock))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			print(error)
			return False

	"""Web frontend, add new product alias
	"""
	def addProductAlias(self, ean, target, current_user):
		if not self.connect():
			return False
		try:
			self.cursor.execute('INSERT INTO product_alias (ean, target) VALUES (%s, %s)', (ean, target))
			self.cursor.execute('INSERT INTO eventlog (user, action) VALUES (%s, "New product alias: %s -> %s")', (current_user, ean, target))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			print(error)
			return False
