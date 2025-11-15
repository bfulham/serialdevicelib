import socket
import json
from pprint import pprint
import logging
import functions

log = logging.getLogger("serialdevicelib_device")

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(message)s")

class serial_device:
    def __init__(self, ip, port, control_ID, group_ID, biblefile):
        self.ip = ip
        self.port = port
        self.control_ID = str(control_ID).zfill(2)
        self.group_ID = str(group_ID).zfill(2)
        self.bible = json.loads(open(biblefile).read())
        self.data = {}

    def connect(self):
        host = self.ip
        port = self.port
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log.info("Connecting to %s on port %s", host, port)
        try:
            self.connection.connect((host, port))
        except:
            log.warning("\033[91mConnection failed\033[0m")
            exit()
        log.info("\033[92mConnected\033[0m")

    def disconnect(self):
        log.info("Disconnecting")
        self.connection.close()
        log.warning("\033[91mDisconnected\033[0m")

    def get(self, command: str, *args: int):
        log.info("Sending data")
        hex = functions.Generate_Command(self.control_ID, self.group_ID, functions.retrieve_command(command, "Get", self.bible), self.bible, args)
        self.connection.send(bytes.fromhex(hex))
        log.info("Waiting for response")
        data_temp = str(self.connection.recv(1024).hex())
        data = data_temp.replace("\\x", "").replace("b'", "").replace("'", "").upper()
        log.info('Received: %s', data)
        return functions.Decode_Hex(data, self.bible)

    def set(self, command: str, *args: int):
        log.info("Sending data")
        hex = functions.Generate_Command(self.control_ID, self.group_ID, functions.retrieve_command(command, "Set", self.bible), self.bible, args)
        self.connection.send(bytes.fromhex(hex))
        log.info("Waiting for response")
        data_temp = str(self.connection.recv(1024).hex())
        data = data_temp.replace("\\x", "").replace("b'", "").replace("'", "").upper()
        log.info('Received: %s', data)
        return functions.Decode_Hex(data, self.bible)
    
    def getOptions(self, command: str):
        return self.bible[functions.retrieve_command(command, "Get", self.bible)]['command']
    
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