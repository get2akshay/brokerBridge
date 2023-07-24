import logging
# Set up logging configuration
logging.basicConfig(level=logging.INFO)  # Set the default log level to DEBUG
# Create a logger instance
logger = logging.getLogger(__name__)
def chirpDeviceDownlink():
    import paho.mqtt.client as mqtt

    # ChirpStack MQTT broker details
    BROKER_HOST = '192.168.1.220'
    BROKER_PORT = 1883

    # Device EUI and downlink payload
    DEVICE_EUI = 'ff82002000000033'
    DOWNLINK_PAYLOAD = 'fa050508030015'  # Example payload

    # MQTT topic for the downlink message
    # DOWNLINK_TOPIC = f'application/YOUR_APPLICATION_ID/device/{DEVICE_EUI}/down'
    DOWNLINK_TOPIC = f"application/dbd25382-10fc-4462-b5c1-8af7bff7d011/device/{DEVICE_EUI}/command/down"

    # Create an MQTT client instance
    client = mqtt.Client()

    # Connect to the MQTT broker
    client.connect(BROKER_HOST, BROKER_PORT, 60)

    # Publish the downlink message
    client.publish(DOWNLINK_TOPIC, payload=DOWNLINK_PAYLOAD, qos=1)
    


def paketSetGpio(gpio=None, on=False):
    header = 0xfa
    length = 0
    factor0x = 0
    cmd = 0x05
    pin = 0x08
    if gpio is not None and gpio == 2:
        pin = 0x09
    ioMode = 0x03
    state = 0x00
    if on:
        state = 0x01
    checksum = 0x0000
    data = [ cmd, pin, ioMode, state]
    for b in data:
        length += len(hex(b))
        factor0x += 2

    length = length - factor0x + 1
    logger.debug(length)
    data.insert(0, length)
    sum = 0x0000
    for s in data:
        sum += s

    data.append(sum)
    data.insert(0, header)
    # Convert list to hex string
    hex_string = ''.join(format(i, '02x') for i in data)
    return hex_string

def paketGetGpio(gpio=None):
    header = 0xfa
    length = 0
    factor0x = 0
    cmd = 0x03
    pin = 0x08
    if gpio is not None and gpio == 2:
        pin = 0x09
    # ioMode = 0x01
    # state = 0x00
    data = [ cmd, pin ]
    for b in data:
        length += len(hex(b))
        factor0x += 2

    length = length - factor0x + 1
    # logger.debug(length)
    data.insert(0, length)
    sum = 0x00
    for s in data:
        sum += s

    data.append(sum)
    data.insert(0, header)
    # Convert list to hex string
    hex_string = ''.join(format(i, '02x') for i in data)
    return hex_string

def base64ToHex(base64_string):
    import base64
    bytes_data = base64.b64decode(base64_string)
    return bytes_data.hex()

def hexToBase64(hex_string):
    import base64
    # Convert the hexadecimal string to bytes
    bytes_data = bytes.fromhex(hex_string)
    # Encode the bytes in Base64 format
    return base64.b64encode(bytes_data).decode()


def encode(data):
    """To encode message
    Example:    {"command": "05", 
      "PIN": "D1", "mode": "03", "state": true}
    """
    # payload = json.loads(data)
    if data.get("method") == "getGpioStatus":
        hexCommand = paketGetGpio(gpio=data["params"]["pin"])
    if data.get("method") == "setGpioStatus":
        hexCommand = paketSetGpio(gpio=data["params"]["pin"], on=data["params"]["enabled"])
    
    out = {
    "devEui": "ff82002000000033",             
    "confirmed": False,                     
    "fPort": 1,
    "data": hexToBase64(hexCommand)                             
    # "data": "+gUFCAMBFg=="                         
    }
    return out
        


def decode(base64_string):
    #Heart Beat done
    #Response - fa050508030116
    import json
    full = dict()
    useFull = dict()
    json_string = '{}'
    attribute = False
    telemetery = False
    rpc_response = False
    hexdata = base64ToHex(base64_string)
    logger.debug(hexdata)
    header = hexdata[:2]
    length = hexdata[2:4]
    command = hexdata[4:6]
    lengthInt = int(length, 16)
    data = hexdata[6:6+ lengthInt +1 ]
    checkSum = hexdata[6+ lengthInt +1: 6+ lengthInt +1 + 2 ]
    full = {"header": header, "length": lengthInt, "command": command, "data": data, "checkSum": checkSum}
    logger.debug(f"Device Response parse {full}")
    if command == "07":
        logger.debug(f"HeartBeat packet - {full}")
        useFull = {"BatteryLife": int(data[:2], 16), "ReportingInterval": int(data[2:6], 16)}
        attribute = True
        # Serialize the JSON object to a string
        json_string = json.dumps(useFull)
    if command == "05":
        if data[:2] == "08":
            useFull["pin"] = 1
            useFull["mode"] = data[2:4]
            useFull["enabled"] = False
            if data[4:6] == "01":
                useFull["enabled"] = True    
        if data[:2] == "09":
            useFull["pin"] = 2
            useFull["mode"] = data[2:4]
            useFull["enabled"] = False
            if data[4:6] == "01":
                useFull["enabled"] = True
        # Serialize the JSON object to a string
        json_string = json.dumps(useFull)
        attribute = True
    if command == "03":
        """fa050309030115"""
        if data[:2] == "08":
            useFull["pin"] = 1
            useFull["mode"] = data[2:4]
            useFull["enabled"] = False
            if data[4:6] == "01":
                useFull["enabled"] = True    
        if data[:2] == "09":
            useFull["pin"] = 2
            useFull["mode"] = data[2:4]
            useFull["enabled"] = False
            if data[4:6] == "01":
                useFull["enabled"] = True
        rpc_response = True
        # Serialize the JSON object to a string
        template = {"method": "getGpioStatus", "params": useFull}
        json_string = json.dumps(template)
    if not json_string:
        attribute, telemetery = False
    return (json_string, attribute, telemetery, rpc_response)

