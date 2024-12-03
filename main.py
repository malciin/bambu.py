import ssl
import json
import paho.mqtt.client as mqtt
import secret

msg_i = 0

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe(f"device/{secret.SERIAL_NUMBER}/report")

def on_message(client, userdata, msg: bytes):
    global msg_i

    decoded = msg.payload.decode('utf8')
    print(f'[{msg_i:06}] {msg.topic}: {decoded}')
    json_object = json.loads(decoded)
    with open(f'mqtt/{msg_i:06}.json', 'w', encoding='utf8') as f:
        f.write(json.dumps(json_object, indent=2))
    msg_i += 1

def connect_fail_callback(client, userdata):
    print('fail')

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print('dc', disconnect_flags, properties, reason_code)
    pass

def on_log(client, userdata, level, buf):
    print(level, buf)

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    protocol=mqtt.MQTTv311)
client.tls_set(cert_reqs=ssl.CERT_NONE) # https://github.com/eclipse-paho/paho.mqtt.python/issues/85#issuecomment-250612020
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message
# client.on_log = on_log
client.on_connect_fail = connect_fail_callback
client.on_disconnect = on_disconnect
client.username_pw_set('bblp', secret.ACCESS_CODE)
client.connect(secret.IP, 8883)
client.loop_forever()