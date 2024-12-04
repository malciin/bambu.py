import argparse
import asyncio
import core
import core.mqtt_channel
import core.bambu_mqtt_credentials
from core.utilities import get_or_none
from win11toast import toast

started = False

async def handle(channel: core.mqtt_channel.Channel):
    global started

    async for msg in channel:
        if 'print' not in msg: continue

        print_object = msg['print']
        gcode_state = get_or_none(print_object, 'gcode_state')
        print_in_progress = ('mc_print_line_number' in print_object and gcode_state == None) or gcode_state == 'PREPARE' or gcode_state == 'RUNNING'
        print_done = gcode_state == 'FINISH' or gcode_state == 'FAILED' or (get_or_none(print_object, 'command') == 'stop' and get_or_none(print_object, 'result') == 'success')

        if started and print_done:
            print('Detected end! Firing notification')
            toast('Print job', 'Print job completed!')
            started = False

        if not started and print_in_progress:
            started = True
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
