import settings
import uuid
from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo

class HomeAssistantMQTT:
	productSensors = {}

	def __init__(self):
			MAC = '%012x' % uuid.getnode()
			for i in range(1, 6):
				MAC = '%s:%s' % (MAC[:i * 3 - 1], MAC[i * 3 - 1:])
			self.dev_id = settings.dev_name.replace(' ','-')
			self.settings = Settings.MQTT(host=settings.mqtt_host, username=settings.mqtt_user, password=settings.mqtt_password)
			self.device = DeviceInfo(name=settings.dev_name, manufacturer='LeineLab', model='NFC Kasse', identifiers=MAC)
			self.stateSensor = Sensor(Settings(mqtt=self.settings, entity=SensorInfo(name='State', unique_id='nfckasse_'+self.dev_id+'_state', device=self.device)))
			self.stateSensor.set_state('idle')

	def setState(self, state):
		self.stateSensor.set_state(state)

	def updateProduct(self, product):
		if product['ean'] not in self.productSensors:
			self.productSensors[product['ean']] = {}
			self.productSensors[product['ean']]['stock'] = Sensor(Settings(mqtt=self.settings, entity=SensorInfo(name=product['name']+' Stock', unique_id='nfckasse_'+product['ean']+'_stock', unit_of_measurement="pcs", device=self.device)))
			self.productSensors[product['ean']]['price'] = Sensor(Settings(mqtt=self.settings, entity=SensorInfo(name=product['name']+' Price', unique_id='nfckasse_'+product['ean']+'_price', device_class="monetary", unit_of_measurement="EUR", device=self.device)))
		self.productSensors[product['ean']]['stock'].set_state(product['stock'])
		self.productSensors[product['ean']]['price'].set_state(product['price'])
