from __future__ import annotations
import json
import ssl
import paho.mqtt.client as mqtt
import secret
import asyncio
from dataclasses import dataclass

@dataclass
class UserData:
    connection_future: asyncio.Event
    queue: asyncio.Queue
    loop: asyncio.AbstractEventLoop

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

async def __set_event(event: asyncio.Event):
    if event.is_set(): return
    event.set()

def __on_connect(client, userdata: UserData, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    asyncio.run_coroutine_threadsafe(__set_event(userdata.connection_future), userdata.loop)
    client.subscribe(f"device/{secret.SERIAL_NUMBER}/report")

def __on_message(client, userdata: UserData, msg: bytes):
    decoded = msg.payload.decode('utf8')
    json_object = json.loads(decoded)
    asyncio.run_coroutine_threadsafe(userdata.queue.put(json_object), userdata.loop)

def __connect_fail_callback(client, userdata: UserData):
    print('fail')

def __on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print('dc', disconnect_flags, properties, reason_code)
    pass

def __on_log(client, userdata, level, buf):
    pass

async def open() -> Channel:
    message_queue = asyncio.Queue()
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        protocol=mqtt.MQTTv311)
    message_channel = Channel(client, message_queue)
    user_data = UserData(
        connection_future=asyncio.Event(),
        queue=message_queue,
        loop=asyncio.get_running_loop())
    client.user_data_set(user_data)

    client.tls_set(cert_reqs=ssl.CERT_NONE) # https://github.com/eclipse-paho/paho.mqtt.python/issues/85#issuecomment-250612020
    client.tls_insecure_set(True)
    client.on_connect = __on_connect
    client.on_message = __on_message
    client.on_log = __on_log
    client.on_connect_fail = __connect_fail_callback
    client.on_disconnect = __on_disconnect
    client.username_pw_set('bblp', secret.ACCESS_CODE)
    client.connect(secret.IP, 8883)
    client.loop_start()

    await user_data.connection_future.wait()

    return message_channel
