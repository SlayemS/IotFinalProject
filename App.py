import dash
import RPi.GPIO as GPIO
from dash import Dash, dcc, html, Input, Output, DiskcacheManager, CeleryManager, callback
from gpiozero import LED
import time
import Freenove_DHT as DHT
import dash_daq as daq
import smtplib, ssl
import imaplib
import email
from email.header import decode_header
import dash_bootstrap_components as dbc
import paho.mqtt.client as mqtt
import sqlite3



GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

Motor1 = 15 # Enable Pin GPIO 22
Motor2 = 13 # Input Pin GPIO 27
Motor3 = 11 # Input Pin GPIO 17
LED = 37
DHTPin = 29 # Define the pin of DHT11

GPIO.setup(LED, GPIO.OUT)
GPIO.setup(Motor1,GPIO.OUT)
GPIO.setup(Motor2,GPIO.OUT)
GPIO.setup(Motor3,GPIO.OUT)

sender_email = "iotprojectemail1@gmail.com"
receiver_email = "jerichonieva.789@gmail.com"
password = "xhym qvsv srmj zfav"
smtp_server = "smtp.gmail.com"

fan_on_image = "https://cdn.dribbble.com/users/3892547/screenshots/11096911/media/e953f570282731a9e81adb0f560d6627.gif"
fan_off_image = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fcdn4.vectorstock.com%2Fi%2Fthumb-large%2F67%2F08%2Felectric-fan-vector-4326708.jpg&f=1&nofb=1&ipt=d80d3713cff90fbfedeca90d9ed670bde56fbd4a53ac5e5371a0f2bbd87f419d&ipo=images"

led_off_image = "https://cdn.icon-icons.com/icons2/2248/PNG/512/led_off_icon_138425.png"
led_on_image = "https://cdn.icon-icons.com/icons2/2248/PNG/512/led_on_icon_138424.png"

email_sent = False
fan_status = False

dht = DHT.DHT(DHTPin)

client = mqtt.Client()

app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# View of our app
app.layout = dbc.Container([
    dbc.Row([
        html.H1("IoT Final Project Dashboard"),
        html.Hr(),
        dbc.Col(
            html.Div(
                children=[
                    dbc.Row(html.Img(src="https://static.vecteezy.com/system/resources/previews/020/765/399/non_2x/default-profile-account-unknown-icon-black-silhouette-free-vector.jpg")),
                    html.Div(id="user_id", children="User ID:"),
                    html.Div(id="name", children="Name:"),
                    html.Div("Favorites:"),
                    html.Div(id="temp_thresh", children="Temperature:"),
                    html.Div(id="hum_thresh", children="Humidity:"),
                    html.Div(id="light_thresh", children="Light Intensity:"),
                ],
            ),
            md=3,
            style={"border":"2px black solid"}
        ),
        dbc.Col(
            dbc.Row([
                html.Div(),
                html.Br(),
                html.Br(),
                daq.Gauge(
                    id='temperature-gauge',
                    label="Temperature",
                    size=160,
                    value=0,  # Initial value
                    max=100,
                    showCurrentValue=True,
                    color={"gradient": True, "ranges": {"blue": [0, 33], "yellow": [33, 66], "red": [66, 100]}}
                ),
                daq.Gauge(
                    id='humidity-gauge',
                    size=160,
                    label="Humidity",
                    value=0,  # Initial value
                    max=100,
                    showCurrentValue=True,
                    color={"gradient": True, "ranges": {"blue": [0, 33], "yellow": [33, 66], "red": [66, 100]}}
                ),
                dcc.Interval(
                    id='interval-component',
                    interval=2000,  # Update every 2 seconds
                    n_intervals=0
                ),
                dcc.Interval(
                    id='receive_reply',
                    interval=5000,  # Update every 5 seconds
                    n_intervals=0
                ),
                dcc.Interval(
                    id='update_light_intensity',
                    interval=3000,  # Update every 3 seconds
                    n_intervals=0
                ),
                dcc.Interval(
                    id='update_user_information',
                    interval=3000,  # Update every 3 seconds
                    n_intervals=0
                ),
            ]),
            md=5,
            style={"border":"2px black solid"}
        ),
        dbc.Col([                
            dbc.Row(
                [
                    html.Img(src=led_off_image, id='ledImg',
                            style={"height":'50%', "width":'50%', "text-Align":"center"}),
                    html.Div(id="light-intensity2", children="Light intensity"),
                    html.Div(id="light-intensity", children=""),
                    html.Div(id="led-status", children="LED Status: OFF"),
                    html.Div(id="email-status", children=""),
                    html.Br(),
                    html.Br(),
                    html.Img(id='fan-gif', style={'width': '200px', 'height': '200px'}, src=fan_off_image),
                    html.Div(id='fan-status-indicator', children="Fan Status: OFF"),        
                ],
                justify="center",  # Center items horizontally
                align="center",  # Center items vertically
            ),                        
        ],
        md=4,
        style={"border":"2px black solid", "text-align": "center"}   
        )       
    ])
])
 
@callback(
    [Output('temperature-gauge', 'value'), Output('humidity-gauge', 'value')],
    Input('interval-component', 'n_intervals'),
    prevent_initial_call=True
)

def update_gauge_value(n_intervals):
    global email_sent
    counts = 0  # Measurement counts
    temperature = 0.0
    humidity = 0.0
    for i in range(0, 15):
        chk = dht.readDHT11()
        if chk is dht.DHTLIB_OK:
            temperature = dht.temperature
            humidity = dht.humidity
            break
        time.sleep(0.1)
        
    if temperature > 24 and not email_sent:
        send_temp_email(temperature)
    elif temperature <= 24:
        email_sent = False
        
    return temperature, humidity

def send_temp_email(temperature):
    global email_sent
    if temperature > 24 and not email_sent:
        port = 587  # For starttls
        message = """\
        Subject: Temperature

        The current temperature is above 24. Would you like to turn on the fan?"""

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  
            server.starttls(context=context)
            server.ehlo()  
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
        email_sent = True
        
@app.callback(
    Output('fan-status-indicator', 'children'),  # Update the content of an element with id 'fan-status-indicator'
    Input('receive_reply', 'n_intervals'),
    prevent_initial_call=True
)

def update_fan_status(n_intervals):
    global email_sent, fan_status
    read_email_reply()
    if fan_status:
        GPIO.output(Motor1,GPIO.HIGH)
        GPIO.output(Motor2,GPIO.HIGH)
        GPIO.output(Motor3,GPIO.LOW)  # Turn on the fan
        return "Fan Status: ON"
    else:
        GPIO.output(Motor1,GPIO.LOW)
        GPIO.output(Motor2,GPIO.LOW)
        GPIO.output(Motor3,GPIO.LOW)  # Turn off the fan
        return "Fan Status: OFF"

@app.callback(
     Output('fan-gif', 'src'),
     Input('fan-status-indicator', 'children'),
     prevent_initial_call=True
)

def update_fan_gif(status):
    if "ON" in status:
        return fan_on_image
    else:
        return fan_off_image
    
def read_email_reply():
    global fan_status
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(sender_email, password)

    mail.select("inbox")

    status, email_ids = mail.search(None, "(UNSEEN)")  # Fetch only unread emails
    print(email_ids)
    email_ids = email_ids[0].split()

    if email_ids:
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

        msg = email.message_from_bytes(msg_data[0][1])

        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                email_body = part.get_payload(decode=True).decode("utf-8")
                print("Email Body:")
                print(email_body)
                if email_body.lower().strip().startswith("yes"):
                    fan_status = not fan_status  # Toggle fan status
                else:
                    print("Email does not start with 'yes'")
    mail.logout()

# Phase 3 Code

@app.callback(
    Output('light-intensity', 'children'),
    Input('update_light_intensity', 'n_intervals'), # every 3 seconds
    prevent_initial_call=True
)
def update_light_intensity(n_intervals):
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("192.168.151.1", 1883, 60) # Change IP Address of mqtt
    
    on_connect
    on_message
        
    client.loop_start()
    time.sleep(3)
    client.loop_stop()
    
    

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("IoTPhase3/LightIntensity")
    client.subscribe("IoTPhase4/RFID")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global light_intensity
    global received_user_id
    global user_user_id
    global user_name 
    global user_temperature
    global user_humidity
    global user_light_intensity
    if msg.topic == "IoTPhase3/LightIntensity":
        light_intensity = float(msg.payload)
        print(f"Current Light Intensity: {light_intensity}")
    elif msg.topic == "IoTPhase4/RFID":
        con = sqlite3.connect("IotProject.db")
        cur = con.cursor()
        received_user_id = msg.payload.decode("utf-8")
        print(f"RFID Message Received: {received_user_id}")
        res = cur.execute("SELECT * FROM User WHERE User_id= " + "'" + received_user_id + "'")
        user = res.fetchone()

        user_user_id = "User ID: "+ str(user[0])
        user_name = "Name: "+ str(user[1])
        email_name = user[1]
        user_temperature = "Temperature: "+ str(user[2])
        user_humidity = "Humidity: "+ str(user[3])
        user_light_intensity = "Light Intensity: "+ str(user[4])
        con.commit()
        con.close()
        port = 587  # For starttls
        message = f"""\
        Subject: User Entered 

        {email_name} has entered at this time."""

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
        

        
        
@app.callback(
    [Output('user_id', 'children'), Output('name', 'children'), Output('temp_thresh', 'children'), Output('hum_thresh', 'children'), Output('light_thresh', 'children')],
    Input('update_user_information', 'n_intervals'),
    prevent_initial_call=True
)
def updateProfileInfo(n_intervals):
    return user_user_id, user_name, user_temperature, user_humidity, user_light_intensity

@app.callback(
    [Output('led-status', 'children'), Output('email-status', 'children'), Output('ledImg', 'src'), Output('light-intensity2','children')],
    Input('update_light_intensity', 'n_intervals'),
    prevent_initial_call=True
)
def update_led_status(n_intervals):
    if light_intensity < 700:
        send_led_email()
        GPIO.output(LED, GPIO.HIGH)  # Turn on the LED
        return "LED Status: ON", "Email has been sent", led_on_image, light_intensity
    else:
        GPIO.output(LED, GPIO.LOW)  # Turn off the LED
        return "LED Status: OFF", "", led_off_image, light_intensity

def send_led_email():
    global email_sent
    port = 587  # For starttls
    message = """\
    Subject: LED Status

    The LED has been turned on."""

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

if __name__ == '__main__':
    app.run(debug=True)
