from __future__ import annotations
import json
import ssl
import paho.mqtt.client as mqtt
import asyncio
from dataclasses import dataclass
from core.bambu_mqtt_credentials import BambuMqttCredentials
from core.utilities import set_future

@dataclass
class UserData:
    connection_future: asyncio.Future[bool]
    message_future: asyncio.Future[bool]
    queue: asyncio.Queue
    loop: asyncio.AbstractEventLoop
    credentials: BambuMqttCredentials

class Channel:
    def __init__(self, client: mqtt.Client, message_queue: asyncio.Queue):
        self.__client = client
        self.__message_queue = message_queue

    def read(self):
        return self.__message_queue.get()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.__client.loop_stop()

    def __aiter__(self):
        return self

    def __anext__(self):
        return self.__message_queue.get()

async def open(credentials: BambuMqttCredentials) -> Channel:
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        protocol=mqtt.MQTTv311)

    message_queue = asyncio.Queue()
    message_channel = Channel(client, message_queue)
    user_data = UserData(
        connection_future=asyncio.Future(),
        message_future=asyncio.Future(),
        queue=message_queue,
        loop=asyncio.get_running_loop(),
        credentials=credentials)

    client.on_connect = __on_connect
    client.on_message = __on_message
    client.on_log = __on_log
    client.on_connect_fail = __connect_fail_callback
    client.on_disconnect = __on_disconnect

    client.user_data_set(user_data)
    client.tls_set(cert_reqs=ssl.CERT_NONE) # https://github.com/eclipse-paho/paho.mqtt.python/issues/85#issuecomment-250612020
    client.tls_insecure_set(True)
    client.username_pw_set('bblp', credentials.access_code)
    
    try:
        client.connect(credentials.ip, 8883)
    except TimeoutError:
        print(f'Failed to connect to {credentials.ip}. Timeout error')
        exit(1)
    client.loop_start()
    connection_success = await user_data.connection_future
    message_success = await user_data.message_future

    if not connection_success: exit(1) 
    if not message_success: exit(2) 

    return message_channel

def __on_connect(client, userdata: UserData, flags, reason_code, properties):
    if reason_code == 'Not authorized':
        print(f'Failed to connect to {userdata.credentials.ip}. Bad access code!')
        set_future(userdata.connection_future, False, userdata.loop)
        return

    print(f"Connected with result code {reason_code}")
    client.subscribe(f"device/{userdata.credentials.serial_number}/report")
    set_future(userdata.connection_future, True, userdata.loop)

def __on_message(client, userdata: UserData, msg: bytes):
    # if we received any message then everything works
    set_future(userdata.message_future, True, userdata.loop)
    decoded = msg.payload.decode('utf8')
    json_object = json.loads(decoded)
    asyncio.run_coroutine_threadsafe(userdata.queue.put(json_object), userdata.loop)

def __connect_fail_callback(client, userdata: UserData):
    print(f'Failed to connect to {userdata.credentials.ip}. Trying to reconnect...')

def __on_disconnect(client, userdata: UserData, disconnect_flags, reason_code, properties):
    # if we disconnected before receiving any message its a sign of bad serial code
    if not userdata.message_future.done():
        print('Bad serial number!')
        set_future(userdata.message_future, False, userdata.loop)

def __on_log(client, userdata, level, buf):
    pass