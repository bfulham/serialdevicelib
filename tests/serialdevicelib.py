import serialdevicelib
from pprint import pprint
TV = serialdevicelib.serial_device("10.0.0.123", 5000, 1, 0, "data.json")
TV.connect()
TV.updateAll()
pprint(TV.data)
#print(TV.get("Failover"))
TV.disconnect()