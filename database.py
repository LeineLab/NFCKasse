import mysql.connector
import uuid
import bcrypt

class Database:
	def __init__(self, **kwargs):
		self.db = mysql.connector.connect(
			host = kwargs['host'],
			user = kwargs['user'],
			password = kwargs['password'],
			database = kwargs['database']
		)
		#self.db.autocommit = True
		self.cursor = self.db.cursor(dictionary=True)
		self.cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')

	def ping(self):
		self.db.ping(True)

	"""Web frontend check, if user exists
	"""
	def isAdmin(self, name):
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
		self.cursor.execute('SELECT password FROM admins WHERE username = %s', (name, ))
		try:
			result = self.cursor.fetchone()
			return bcrypt.checkpw(password.encode('utf-8'), result['password'].encode('utf-8'))
		except mysql.connector.Error as error:
			return False

	"""Web frontend, add new user
	"""
	def addAdmin(self, name, password):
		try:
			salt = bcrypt.gensalt()
			hash = bcrypt.hashpw(password.encode('utf-8'), salt)
			self.cursor.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', (name, hash))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, remove user
	"""
	def deleteAdmin(self, name):
		try:
			self.cursor.execute('DELETE FROM admins WHERE username=%s', (name, ))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, change password of user
	"""
	def changePassword(self, name, password):
		try:
			salt = bcrypt.gensalt()
			hash = bcrypt.hashpw(password.encode('utf-8'), salt)
			self.cursor.execute('UPDATE admins SET password=%s WHERE username=%s', (hash, name))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, list users
	"""
	def getAdmins(self):
		self.cursor.execute('SELECT username, otp_validated as otp FROM admins')
		try:
			results = self.cursor.fetchall()
			return results
		except mysql.connector.Error as error:
			return []

	"""Web frontend, reset OTP for user

	User needs to login after the reset and complete the OTP setup
	"""
	def resetOTP(self, name):
		try:
			self.cursor.execute('UPDATE admins SET otps=NULL, otp_validated=0 WHERE username = %s', (name, ))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, get OTP secret for user
	"""
	def getOTPSecret(self, name):
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
		try:
			self.cursor.execute('UPDATE admins SET otps = %s WHERE username = %s', (secret, name))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Web frontend, check if user has validated the OTP secret
	"""
	def isOTPverified(self, name):
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
		try:
			self.cursor.execute('UPDATE admins SET otp_validated = 1 WHERE username = %s', (name,))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Get product for EAN

	@returns Tuple of (name, price)
	"""
	def getProduct(self, ean):
		self.cursor.execute('SELECT name, price FROM products WHERE ean = %s', (ean, ))
		try:
			result = self.cursor.fetchone()
			return (result['name'], float(result['price']))
		except TypeError:
			return (None, None)
		except mysql.connector.Error as error:
			return (None, None)

	"""Web frontend, get list of products
	"""
	def getProducts(self):
		self.cursor.execute('SELECT p.ean, p.name, p.price, p.stock, IFNULL(t1.sales_7d, 0) as sales_7d, IFNULL(t2.sales_30d, 0) as sales_30d FROM products p LEFT JOIN (SELECT count(tid) AS sales_7d, ean FROM transactions WHERE ean IS NOT NULL AND tdate >= DATE_SUB(now(), INTERVAL 7 DAY) GROUP BY ean) t1 ON p.ean = t1.ean LEFT JOIN (SELECT count(tid) AS sales_30d, ean FROM transactions WHERE ean IS NOT NULL AND tdate >= DATE_SUB(now(), INTERVAL 30 DAY) GROUP BY ean) t2 ON p.ean = t2.ean')
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
		try:
			self.cursor.execute('INSERT INTO cards (uid) VALUES (%s)', (hash, ))
			result = self.db.commit()
			return True
		except mysql.connector.Error as error:
			return False

	"""Check if card is registered and return value
	"""
	def getCard(self, hash):
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
		try:
			self.cursor.execute('SELECT uid, value FROM cards')
			results = self.cursor.fetchall()
			return results
		except mysql.connector.Error as error:
			return []
		return []

	"""Web frontend, get total credits of all cards
	"""
	def getBalance(self):
		try:
			self.cursor.execute('SELECT COALESCE(SUM(value),0) as totalvalue FROM cards')
			result = self.cursor.fetchone()
			return result['totalvalue']
		except mysql.connector.Error as error:
			return 0
		return 0

	"""Web frontend, get total topup value not redeemed
	"""
	def getTopupBalance(self):
		try:
			self.cursor.execute('SELECT COALESCE(SUM(value),0) as totalvalue FROM topups WHERE used=0')
			result = self.cursor.fetchone()
			return result['totalvalue']
		except mysql.connector.Error as error:
			return 0
		return 0

	"""Web frontend, generate topup hash for a given amount
	"""
	def generateTopUp(self, amount):
		try:
			code = uuid.uuid4().hex
			print(code)
			self.cursor.execute('INSERT INTO topups (code, value, created_on) VALUES (%s, %s, NOW())', (code, amount))
			self.db.commit()
			return code
		except TypeError:
			return None

	"""Check if topup code is existing

	@return Tuple of (value, used)
	"""
	def checkTopUp(self, code):
		try:
			self.cursor.execute('SELECT value, used FROM topups WHERE code = %s', (code, ))
			result = self.cursor.fetchone()
			print(result['value'], result['used'])
			return result['value'], result['used']
		except TypeError:
			return None, None

	"""Redeem topup code for card
	"""
	def topUpCard(self, cardhash, code):
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

	"""Increase or reduce product stock
	"""
	def changeProductStock(self, ean, amount):
		try:
			self.cursor.execute('UPDATE products SET stock = stock + (%s) WHERE ean = %s', (amount, ean))
			self.db.commit()
			return self.cursor.rowcount != 0
		except mysql.connector.errors.DataError:
			return False

	"""Web frontend, change product price
	"""
	def changeProductPrice(self, ean, price):
		try:
			self.cursor.execute('UPDATE products SET price = (%s) WHERE ean = %s', (price, ean))
			self.db.commit()
			return self.cursor.rowcount != 0
		except mysql.connector.errors.DataError:
			return False

	"""Buy a product, deduct stock and card value, create transaction
	"""
	def buyProduct(self, cardhash, ean):
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

	"""Web frontend, add new product
	"""
	def addProduct(self, ean, name, price, stock):
		try:
			self.cursor.execute('INSERT INTO products (ean, name, price, stock) VALUES (%s, %s, %s, %s)', (ean, name, price, stock))
			self.db.commit()
			return True
		except mysql.connector.Error as error:
			print(error)
			return False
