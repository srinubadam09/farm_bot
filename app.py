from flask import Flask, render_template, request, Response, redirect, url_for
import paho.mqtt.client as mqtt
import time
import socket

app = Flask(__name__)

# MQTT setup
BROKER = "35.154.62.193"
PORT = 1883
TOPIC_COMMAND = "farmbot/command"
TOPIC_SOIL = "farmbot/soil"

soil_value = "No data yet"

# --- MQTT callbacks ---
def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT with result code " + str(rc))
    client.subscribe(TOPIC_SOIL)

def on_message(client, userdata, msg):
    global soil_value
    if msg.topic == TOPIC_SOIL:
        soil_value = msg.payload.decode()
        print("🌱 Soil Moisture:", soil_value)

# MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

# ----------------- Flask routes ------------------

# Welcome page
@app.route("/")
def welcome():
    return render_template("welcome.html")

# Servo control page
@app.route("/control")
def control():
    return render_template("control.html")

# Soil moisture page
@app.route("/moisture")
def moisture():
    return render_template("moisture.html")

# Send command to ESP
@app.route("/command", methods=["POST"])
def command():
    action = request.form.get("action")
    if action:
        client.publish(TOPIC_COMMAND, action)
        print("📤 Sent command:", action)
    return ("", 204)

# Stream soil moisture data (SSE)
@app.route("/stream")
def stream():
    def event_stream():
        last_value = ""
        while True:
            global soil_value
            if soil_value != last_value:
                yield f"data: {soil_value}\n\n"
                last_value = soil_value
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

# Redirect /home → /
@app.route("/home")
def home_redirect():
    return redirect(url_for("welcome"))

# Helper to get local IP for mobile access
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# Run server
if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"🌍 Access the app on: http://{local_ip}:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

