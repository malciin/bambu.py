"""
    Sends windows 10/11 toast messages about printing end
"""

import argparse
import asyncio
import core
import core.mqtt_channel
import core.bambu_mqtt_credentials
import os
from win11toast import toast
from core.bootstrapper import Bootstrapper

printing_started = False
notification_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'resources',
    'notification.en.wav')

async def handle(channel: core.mqtt_channel.Channel):
    global printing_started

    async for msg in channel:
        if 'print' not in msg: continue

        if printing_started and core.is_not_printing_for_sure(msg):
            print('Detected end! Firing notification')
            toast('Print job', 'Print job completed!', audio=notification_path)
            printing_started = False

        if not printing_started and core.is_printing_for_sure(msg):
            printing_started = True
            print('Detected inprogress print')

async def main(args: argparse.Namespace):
    with await core.mqtt_channel.open(core.bambu_mqtt_credentials.parse(args)) as ch:
        try:
            await handle(ch)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print('Stopping...')
    print('Bye!')

bootstrapper = Bootstrapper(script_description='Sends Windows 10/11 toast notifications when printing is complete.')
bootstrapper.run(main)
