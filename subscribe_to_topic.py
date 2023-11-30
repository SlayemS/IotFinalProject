import paho.mqtt.client as mqtt
import time

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("IoTPhase3/LightIntensity")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    return msg.topic+" "+str(msg.payload)

client = mqtt.Client()
client.connect("10.0.0.90", 1883, 60) # Change IP Address of mqtt

client.on_connect = on_connect
client.on_message = on_message


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.loop_forever()

client.loop_start()
time.sleep(3)
client.loop_stop()
