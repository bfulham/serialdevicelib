import logging
from pprint import pformat

log = logging.getLogger("serialdevicelib")

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s")

def Generate_Checksum(data: str):
    a = data
    b = [a[i:i+2] for i in range(0, len(a), 2)] # ['10', 'F8', '00', ...
    sum = "0"
    for i in b:
        sum = hex(int(sum, 16) ^ int(i, 16))
    return str(sum).replace("0x", "").upper().zfill(2)

def Generate_Command(Control_ID: str, Group: str, Command: str, bible, Data: tuple[int, ...]):
    temp_command = ""
    temp_command += str(len(Data) + 5).zfill(2)
    temp_command += Control_ID
    temp_command += Group
    temp_command += Command
    for i in Data:
        temp_command += f"{i:02x}"
    Full_command = temp_command + Generate_Checksum(temp_command)
    log.info("Command: %s", Full_command)
    Decode_Hex(Full_command, bible, "command")
    return Full_command

def multilist_Generate_Command(Control_ID: str, Group: str, Command: str, bible, Data: dict):
    temp_command = ""
    temp_command += str(len(Data) + 5).zfill(2)
    temp_command += Control_ID
    temp_command += Group
    temp_command += Command
    for index, source in Data.items():
        for key, value in bible[Command]['command']['1']['Options'].items():
            if value == source:
                temp_command += str(key).zfill(2)
    Full_command = temp_command + Generate_Checksum(temp_command)
    log.info("Command: %s", Full_command)
    Decode_Hex(Full_command, bible, "command")
    return Full_command

def Decode_Hex(Hex, bible, Hex_type="response"):
    log.debug("Decoding %s", Hex_type)
    a = Hex
    b = [a[i:i+2] for i in range(0, len(a), 2)] # ['10', 'F8', '00', ...
    control_id = int(b[1])
    log.debug("Control ID: %s", int(control_id))
    group = int(b[2])
    log.debug("Group ID: %s", int(group))
    data = b[3:-1]
    command = data[0]
    checksum = b[-1]
    if  int(Generate_Checksum(Hex[:-2]), 16) == int(checksum, 16):
        log.debug("Checksum OK")
    else:
        log.warning("Checksum failed")
    log.info("Command: %s", bible[command]['name'])
    response = b[4:-1]
    if command in bible:
        to_return = {}
        number = {}
        for byte in bible[command][Hex_type]:
            type = bible[command][Hex_type][byte]['type']
            key = bible[command][Hex_type][byte]['Description']
            match type:
                case "list":
                    to_return[key] = bible[command][Hex_type][byte]['Options'][data[int(byte)]]
                case "bool":
                    to_return[key] = bool(bible[command][Hex_type][byte]['Options'][data[int(byte)]])
                case "number":
                    if bible[command][Hex_type][byte]['Description'] not in number:
                        number[bible[command][Hex_type][byte]['Description']] = {}
                    number[bible[command][Hex_type][byte]['Description']][bible[command][Hex_type][byte]['Position']] = data[int(byte)]
                case "ASCII":
                    string = ""
                    for char in range(len(response)):
                        string += bytes.fromhex(response[char]).decode('ascii')
                    to_return[key] = string
                case "multilist":
                    multilist = {}
                    i = 0
                    for item in data[int(byte):len(data)]:
                        multilist[i] = bible[command][Hex_type]['1']['Options'][item.upper()]
                        i = i + 1
                    to_return[key] = multilist
        numbers = len(number)
        if numbers != 0:
            p = {}
            for i in number:
                p[i] = "0x"
                for n in number[i]:
                    p[i] += number[i][n]
                p[i] = int(p[i], 16)
            to_return[key] = p
    if len(to_return) == 1:
        log.info("Data: %s", list(to_return.values())[0])
        return list(to_return.values())[0]
    else:
        log.info("Data: %s", pformat(to_return))
        return to_return

def check_response(control_ID, group_ID, response):
    a = response
    b = [a[i:i+2] for i in range(0, len(a), 2)] # ['10', 'F8', '00', ...
    size = int(b[0])
    control_id_check = str(b[1]).zfill(2) == control_ID
    group_id_check = str(b[2]).zfill(2) == group_ID
    data = b[3:-1]
    command = data[0]
    checksum_check = int(Generate_Checksum(response[:-2]), 16) == int(b[-1], 16)
    return control_id_check, group_id_check, data, checksum_check

def retrieve_command(command_name: str, type: str, bible) -> str:
    for command in bible:
        if bible[command]["name"] == command_name:
            if bible[command]["type"] == type:
                return command
    return "Command not found"