import paho.mqtt.client as mqtt
import json
from fst.codecFt200 import encode, decode
import logging
# Set up logging configuration
logging.basicConfig(level=logging.INFO)  # Set the default log level to DEBUG
# Create a logger instance
logger = logging.getLogger(__name__)

rpcId = None

def fst200Decode(hex):
    from fst.codecFt200 import decode
    

def dowlinkMessage(msg_for_ground):
    logger.debug("Method will process messages from Sky To Ground!")
    # payload = json.loads(msg_for_ground)
    payload = json.loads(msg_for_ground)
    # Set function
    return encode(payload)
       

def uplinkMessage(msg_from_ground):
    logger.debug("Method will process messages from Ground To Sky!")
    modifiedPayload = []
    payload = json.loads(msg_from_ground)
    if "data" in payload:
        modifiedPayload = decode(payload["data"])
    return modifiedPayload
        

def processGatewayMessage(message):
    logger.debug("Method will process Gateway specific MQTT topics")
    
# Source broker details
SOURCE_BROKER_HOST = '192.168.1.220'
SOURCE_BROKER_PORT = 1883
SOURCE_BROKER_USERNAME = 'lora'
SOURCE_BROKER_PASSWORD = 'lora@652'

# Create a MQTT client instance
ground_client = mqtt.Client()
ground_client.username_pw_set(username="lora", password="lora@652")


def on_connect_chirp(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to ChirpStack")
        # Subscribe to the necessary topics after successful connection
        client.subscribe("#")
    else:
        logger.debug("Connection to ChirpStack failed")

# Callback function for handling messages received from the source broker
def on_message_from_ground(client, userdata, message):
    # Default publish flag set to false to publish only required data
    payload = message.payload
    flag = False
    #logger.info(message.topic)
    # Logic to check if its a Gateway topic or Application Topic
    if "gateway" in message.topic:
        logger.debug(f"Gateway Message from Ground {message.topic}")
        return False # For now only handle Application topic
    if "application" in message.topic and "up" in message.topic and "ff82002000000033" in message.topic:
        logger.debug(f"Device Message from Ground {message.topic}")
        payload = uplinkMessage(message.payload)
        flag = True
    # Forward the message to the destination broker
    if flag and payload != None: 
        if payload[1]:
            message.topic = "v1/devices/me/attributes".encode()
            logger.info(f"Message going to the Sky! {payload} to Topic {message.topic}")
            sky_client.publish(message.topic, payload=payload[0].encode(), qos=message.qos, retain=message.retain)
        if payload[2]:
            message.topic = "v1/devices/me/telemetry".encode()
            logger.info(f"Message going to the Sky! {payload} to Topic {message.topic}")
            sky_client.publish(message.topic, payload=payload[0].encode(), qos=message.qos, retain=message.retain)
        if payload[3]:
           message.topic = f"v1/devices/me/rpc/response/{rpcId}".encode()
           logger.info(f"Message going to the Sky! {payload} to Topic {message.topic}")
           sky_client.publish(message.topic, payload=payload[0].encode(), qos=message.qos, retain=message.retain)
    else:
        logger.debug("Topic will not be published to Sky!")

# Callback function for handling messages received from the source broker
def on_message_from_sky(client, userdata, message):
    logger.info(f"Payload from Sky {message.payload} on topic {message.topic}")
    #Check the Request from Sky
    dic = {}
    groundTopic = 'application/dbd25382-10fc-4462-b5c1-8af7bff7d011/device/ff82002000000033/command/down'
    if "rpc" in message.topic and "request" in message.topic:
        global rpcId
        rpcId = message.topic.split('/').pop()
        logger.debug(f"RPC Request payload: {message.payload}")
        #Process Message for Device - Topic
        groundTopic = 'application/dbd25382-10fc-4462-b5c1-8af7bff7d011/device/ff82002000000033/command/down'
    data = dowlinkMessage(msg_for_ground=message.payload)
    # Forward the message to the destination broker
    payload = json.dumps(data)
    logger.debug(f"To be sent to Device: {data}")
    # ground_client.publish(message.topic, payload=payload, qos=message.qos, retain=message.retain)
    ground_client.publish(groundTopic, payload=payload, qos=1)

# Destination broker details
# ThingsBoard MQTT broker details
THINGSBOARD_HOST = '65.20.78.99'
ACCESS_TOKEN = 'e8lsayg6mxyc8d6wcc74'
# Create a MQTT client instance
sky_client = mqtt.Client()
sky_client.username_pw_set(ACCESS_TOKEN)
# Callback function for connection established
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to ThingsBoard")
        # Subscribe to the necessary topics after successful connection
        client.subscribe("v1/devices/me/rpc/request/+")
    else:
        logger.debug("Connection to ThingsBoard failed")

# Assign the on_connect and on_message callback functions
sky_client.on_connect = on_connect
# Assign the on_connect and on_message callback functions
ground_client.on_connect = on_connect_chirp

# Connect to the ThingsBoard MQTT broker
sky_client.connect(THINGSBOARD_HOST, 1883, 60)
ground_client.connect(SOURCE_BROKER_HOST, 1883, 60)


# Assign the on_message callback function for the source broker client
ground_client.on_message = on_message_from_ground
sky_client.on_message = on_message_from_sky


# Start the MQTT client loop to receive messages
sky_client.loop_start()
ground_client.loop_start()

# Keep the program running
while True:
    pass