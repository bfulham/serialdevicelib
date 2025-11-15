import logging

log = logging.getLogger("serialdevicelib_functions")

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(message)s")

def Generate_Checksum(data: str):
    a = data
    b = [a[i:i+2] for i in range(0, len(a), 2)] # ['10', 'F8', '00', ...
    sum = "0"
    for i in b:
        sum = hex(int(sum, 16) ^ int(i, 16))
    return str(sum).replace("0x", "").upper().zfill(2)

def Generate_Command(Control_ID: str, Group: str, Command: str, bible, Data: int=[]):
    temp_command = ""
    temp_command += str(len(Data) + 5).zfill(2)
    temp_command += Control_ID
    temp_command += Group
    temp_command += Command
    for i in Data:
        temp_command += str(i).zfill(2)
    Full_command = temp_command + Generate_Checksum(temp_command)
    log.debug("Command: %s", Full_command)
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
        log.info("\033[92mChecksum OK\033[0m")
    else:
        log.warning("\033[91mChecksum failed\033[0m")
    log.debug("Command: %s", bible[command]['name'])
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
                    if bible[command][Hex_type][byte]['Group'] not in number:
                        number[bible[command][Hex_type][byte]['Group']] = {}
                    number[bible[command][Hex_type][byte]['Group']][bible[command][Hex_type][byte]['Position']] = data[int(byte)]
                case "ASCII":
                    string = ""
                    for char in range(len(response)):
                        string += bytes.fromhex(response[char]).decode('ascii')
                    to_return[key] = string
                case "multilist":
                    multilist = {}
                    i = 0
                    for item in data[int(byte):len(data)]:
                        multilist[i] = bible[command][Hex_type][byte]['Options'][item]
                        i = i + 1
                    to_return[key] = multilist
        numbers = len(number)
        if numbers != 0:
            p = {}
            if numbers == 1:
                p[0] = "0x"
                for n in number[0]:
                    p[0] += number[0][n]
                p = int(p[0], 16)
            else:
                for i in number:
                    p[i] = "0x"
                    for n in number[i]:
                        p[i] += number[i][n]
                    p[i] = int(p[i], 16)
            to_return[key] = p
    if len(to_return) == 1:
        return list(to_return.values())[0]
    else:
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

def retrieve_command(command_name: str, type: str, bible):
    for command in bible:
        if bible[command]["name"] == command_name:
            if bible[command]["type"] == type:
                return command