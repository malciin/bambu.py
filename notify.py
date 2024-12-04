import argparse
import asyncio
import core
import core.mqtt_channel
import core.bambu_mqtt_credentials
from win11toast import toast

printing_started = False

async def handle(channel: core.mqtt_channel.Channel):
    global printing_started

    async for msg in channel:
        if 'print' not in msg: continue

        if printing_started and core.is_not_printing_for_sure(msg):
            print('Detected end! Firing notification')
            toast('Print job', 'Print job completed!')
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

parser = argparse.ArgumentParser(
    prog='notification.py',
    description='Sends windows 10/11 notifications about printing end.')
core.add_core_arguments(parser)
args = parser.parse_args()
asyncio.run(main(args))
