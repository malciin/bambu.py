import signal
import ssl
import json
import paho.mqtt.client as mqtt
import secret
import subprocess
import shlex
import utilities
from datetime import datetime

recorder: subprocess.Popen[bytes] = None
print_job_name: str = None
file: str = None
layer: int = 0
total_layers = 0
layer_num = 0

def start_recorder():
    global file
    file = f'{datetime.now().strftime("%Y%m%d-%H%M%S")}.avi'
    ffmpeg = subprocess.Popen(shlex.split(
        f'ffmpeg -hide_banner -loglevel error -y -i {secret.RTSP} ' +
        f'-vcodec copy -acodec copy {file} ' + ''))
        # todo: add --ui flag
        # f'-vcodec copy -acodec copy -hls_list_size 5 -hls_flags delete_segments -f hls www/hls.m3u8'))

    print(f'Started recording to {file}')

    return ffmpeg

def stop_recorder(recorder: subprocess.Popen):
    if recorder is None: return # nothing to stop

    # https://github.com/apache/beam/pull/31574/files
    try:
        recorder.send_signal(signal.SIGINT)
    except ValueError:
        recorder.terminate()
    recorder.wait()
    print(f'Created record: {file}')

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe(f"device/{secret.SERIAL_NUMBER}/report")

def on_message(client, userdata, msg: bytes):
    global recorder
    global print_job_name
    global total_layers
    global layer_num

    decoded = msg.payload.decode('utf8')
    json_object = json.loads(decoded)

    # with open(f'log/{datetime.now().strftime("%Y%m%d-%H%M%S.%f")}.json', 'w', encoding='utf8') as f:
    #     f.write(json.dumps(json_object, indent=2))

    if 'info' in json_object: return
    if 'system' in json_object: return
    if 'liveview' in json_object: return
    if 'print' not in json_object:
        print('Unhandled json:', json_object)
        return

    print_object = json_object['print']
    gcode_state = utilities.get_or_none(print_object, 'gcode_state')
    should_start = ('mc_print_line_number' in print_object and gcode_state == None) or gcode_state == 'PREPARE' or gcode_state == 'RUNNING'
    should_end = gcode_state == 'FINISH' or gcode_state == 'FAILED' or (utilities.get_or_none(print_object, 'command') == 'stop' and utilities.get_or_none(print_object, 'result') == 'success')

    # print(should_start, should_end, json_object)

    if 'gcode_file' in print_object:
        print_job_name = print_object['gcode_file']

    if 'total_layer_num' in print_object:
        total_layers = print_object['total_layer_num']

    if 'layer_num' in print_object:
        layer_num = print_object['layer_num']

        if recorder is not None and total_layers != 0:
            print(f'L: {layer_num}/{total_layers}')

    if recorder is not None and should_end:
        stop_recorder(recorder)
        print('Waiting patiently for next print!')
        recorder = None
        print_job_name = None
        total_layers = None
        layer_num = None

    if recorder is None and should_start:
        recorder = start_recorder()

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

try:
    client.loop_forever()
except KeyboardInterrupt:
    print('Stopping MQTT client')
    client.disconnect_callback()

    if recorder is not None:
        print('Stopping FFmpeg recorder')
        stop_recorder(recorder)

    print('Bye!')
except Exception as error:
    print('Crashed!')
    print(error)

    print('Stopping MQTT client')
    client.disconnect_callback()

    if recorder is not None:
        print('Stopping FFmpeg recorder')
        stop_recorder(recorder)
