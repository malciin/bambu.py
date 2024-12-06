"""
    Simple debugging program that dumps all messages from MQTT to ./mqtt folder.
"""

import argparse
import asyncio
import json
import core
import core.mqtt_channel
import core.bambu_mqtt_credentials
import os
from datetime import datetime
from core.bootstrapper import Bootstrapper

async def main(args: argparse.Namespace):
    with await core.mqtt_channel.open(core.bambu_mqtt_credentials.parse(args)) as ch:
        try:
            await handle(ch)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print('Stopping...')
    print('Bye!')

async def handle(channel: core.mqtt_channel.Channel):
    os.makedirs('mqtt', exist_ok=True)
    async for msg in channel:
        msg_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        print(msg_timestamp, msg)
        with open(f'mqtt/{msg_timestamp}.json', 'w', encoding='utf8') as f:
            f.write(json.dumps(msg, indent=2))

bootstrapper = Bootstrapper('Dumps every mqtt messages from printer to mqtt folder.')
bootstrapper.run(main)
