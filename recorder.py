import argparse
import asyncio
import core
import core.bambu_mqtt_credentials
import core.mqtt_channel
import signal
import subprocess
import shlex
from core.utilities import get_or_none
from datetime import datetime

class Recorder:
    def __init__(self, source: str):
        self.file = f'{datetime.now().strftime("%Y%m%d-%H%M%S")}.avi'
        self.ffmpeg = subprocess.Popen(shlex.split(
            f'ffmpeg -hide_banner -loglevel error -y -i {source} ' +
            f'-vcodec copy -acodec copy {self.file} ' + ''))

    def dispose(self):
        # https://github.com/apache/beam/pull/31574/files
        try:
            self.ffmpeg.send_signal(signal.SIGINT)
        except ValueError:
            self.ffmpeg.terminate()

async def main(args: argparse.Namespace):
    recorder_instance: Recorder = None
    print_job_name: str = None
    layer_num = 0
    total_layers = 0
    channel = await core.mqtt_channel.open(core.bambu_mqtt_credentials.parse(args))

    async for msg in channel:
        if 'info' in msg: continue
        if 'system' in msg: continue
        if 'liveview' in msg: continue
        if 'print' not in msg:
            print('Unhandled json:', msg)
            continue

        print_object = msg['print']
        gcode_state = get_or_none(print_object, 'gcode_state')
        should_start = ('mc_print_line_number' in print_object and gcode_state == None) or gcode_state == 'PREPARE' or gcode_state == 'RUNNING'
        should_end = gcode_state == 'FINISH' or gcode_state == 'FAILED' or (get_or_none(print_object, 'command') == 'stop' and get_or_none(print_object, 'result') == 'success')

        if 'gcode_file' in print_object:
            print_job_name = print_object['gcode_file']

        if 'total_layer_num' in print_object:
            total_layers = print_object['total_layer_num']

        if 'layer_num' in print_object:
            layer_num = print_object['layer_num']

            if recorder_instance is not None and total_layers != 0 and print_job_name.endswith('.3mf'):
                print(f'{print_job_name} L: {layer_num}/{total_layers}')

        if recorder_instance is not None and should_end:
            recorder_instance.dispose()
            print(f'File {recorder_instance.file} finished!')
            print('Waiting patiently for next print!')
            recorder_instance = None
            print_job_name = None
            total_layers = None
            layer_num = None

        if recorder_instance is None and should_start:
            recorder_instance = Recorder(args.camera_source)
            print(f'Opening {recorder_instance.file} file')

parser = argparse.ArgumentParser(
    prog='recorder.py',
    description='Creates records from an IP camera using the RT(S)P protocol. Recording begins when printing starts and ends when printing stops or completes.')

core.add_core_arguments(parser)
parser.add_argument('-s', '--camera-source', required=True, help="Camera source. Eg. 'rtp://192.168.1.1' or 'rtsp://user:password@192.168.1.1/stream1'")
args = parser.parse_args()

asyncio.run(main(args))
