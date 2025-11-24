import socket
import json
from pprint import pprint
import logging
from .functions import Generate_Checksum, Generate_Command, Decode_Hex, check_response, retrieve_command

log = logging.getLogger("serialdevicelib")

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s")

class serial_device:
    def __init__(self, ip, port, control_ID = 1, group_ID = 0, biblefile = ".\\data.json"):
        self.ip = ip
        self.port = port
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(5)
        self.control_ID = str(control_ID).zfill(2)
        self.group_ID = str(group_ID).zfill(2)
        self.bible = json.loads(open(biblefile).read())
        self.data = {}

    def connect(self):
        host = self.ip
        port = self.port
        log.info("Connecting to %s on port %s", host, port)
        try:
            self.connection.connect((host, port))
            log.info("Connected")
        except:
            log.warning("Connection failed")

    def disconnect(self):
        log.info("Disconnecting")
        self.connection.close()
        log.warning("Disconnected")

    def get(self, command: str, *args: int):
        log.info("Sending data")
        hex = Generate_Command(self.control_ID, self.group_ID, retrieve_command(command, "Get", self.bible), self.bible, args)
        self.connection.send(bytes.fromhex(hex))
        log.info("Waiting for response")
        data_temp = str(self.connection.recv(1024).hex())
        data = data_temp.replace("\\x", "").replace("b'", "").replace("'", "").upper()
        log.info('Received: %s', data)
        return Decode_Hex(data, self.bible)

    def set(self, command: str, *args: int):
        log.info("Sending data")
        hex = Generate_Command(self.control_ID, self.group_ID, retrieve_command(command, "Set", self.bible), self.bible, args)
        self.connection.send(bytes.fromhex(hex))
        log.info("Waiting for response")
        data_temp = str(self.connection.recv(1024).hex())
        data = data_temp.replace("\\x", "").replace("b'", "").replace("'", "").upper()
        log.info('Received: %s', data)
        return Decode_Hex(data, self.bible)
    
    def getOptions(self, command: str):
        return self.bible[retrieve_command(command, "Get", self.bible)]['command']
    
    def availableGets(self):
        gets = {}
        for command in self.bible:
            if self.bible[command]["type"] == "Get":
                gets[command] = self.bible[command]
        return gets
    
    def availableSets(self):
        sets = {}
        for command in self.bible:
            if self.bible[command]["type"] == "Set":
                sets[command] = self.bible[command]
        return sets
    
    def updateAll(self):
        for command in self.availableGets():
            if len(self.bible[command]["command"]) == 0:
                self.data[self.bible[command]["name"]] = self.get(self.bible[command]["name"])
            for var in self.bible[command]["command"]:
                for opt in self.bible[command]["command"][var]["Options"]:
                    self.data[self.bible[command]["command"][var]["Options"][opt]] = self.get(self.bible[command]["name"], opt)
        return self.data