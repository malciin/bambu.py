"""
    Sends windows 10/11 toast messages about printing end or pause
"""

import argparse
import asyncio
import core
import core.mqtt_channel
import core.bambu_mqtt_credentials
import os
from win11toast import toast
from core.bootstrapper import Bootstrapper

resources_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
print_completed_path = os.path.join(resources_path, 'print-completed.en.wav')
print_paused_path = os.path.join(resources_path, 'print-stopped.en.wav')

async def handle(channel: core.mqtt_channel.Channel):
    printing_started = False
    pause_alert_sent = False

    async for msg in channel:
        if 'print' not in msg: continue

        if printing_started and core.is_not_printing_for_sure(msg):
            print('Detected end! Firing notification')
            toast('Print job', 'Print job completed!', audio=print_completed_path)
            printing_started = False

        if not printing_started and core.is_printing_for_sure(msg):
            printing_started = True
            pause_alert_sent = False
            print('Detected inprogress print')

        if pause_alert_sent and not core.is_not_paused_for_sure(msg):
            print('Pause resolved!')
            pause_alert_sent = False

        if not pause_alert_sent and core.is_paused(msg):
            pause_alert_sent = True
            print('Detected paused print! Firing notification')
            toast('Print job', 'Print paused. Please check your printer!', audio=print_paused_path)

async def main(args: argparse.Namespace):
    with await core.mqtt_channel.open(core.bambu_mqtt_credentials.parse(args)) as ch:
        try:
            await handle(ch)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print('Stopping...')
    print('Bye!')

bootstrapper = Bootstrapper(script_description='Sends Windows 10/11 toast notifications when printing is complete or paused.')
bootstrapper.run(main)
