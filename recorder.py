import argparse
import asyncio
import core
import core.bambu_mqtt_credentials
import core.mqtt_channel
import signal
import subprocess
import shlex
from datetime import datetime
from core.bootstrapper import Bootstrapper

class Recorder:
    @property
    def started(self):
        return self.ffmpeg is not None

    def __init__(self, source: str):
        self.source = source
        self.file: str = None
        self.ffmpeg: subprocess.Popen = None

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if self.started:
            print(f'Gracefully stopping record {self.file}')
        
        self.stop()

    def start(self):
        self.file = f'{datetime.now().strftime("%Y%m%d-%H%M%S")}.avi'
        self.ffmpeg = subprocess.Popen(shlex.split(
            f'ffmpeg -hide_banner -loglevel error -y -i {self.source} ' +
            f'-vcodec copy -acodec copy {self.file} ' + ''))

    def stop(self):
        if not self.started: return

        # https://github.com/apache/beam/pull/31574/files
        try:
            self.ffmpeg.send_signal(signal.SIGINT)
        except ValueError:
            self.ffmpeg.terminate()
        self.ffmpeg = None

async def handle(recorder: Recorder, channel: core.mqtt_channel.Channel):
    print_job_name: str = None
    layer_num = 0
    total_layers = 0

    async for msg in channel:
        if 'info' in msg: continue
        if 'system' in msg: continue
        if 'liveview' in msg: continue
        if 'print' not in msg:
            print('Unhandled json:', msg)
            continue

        print_object = msg['print']

        if 'gcode_file' in print_object:
            print_job_name = print_object['gcode_file']

        if 'total_layer_num' in print_object:
            total_layers = print_object['total_layer_num']

        if 'layer_num' in print_object:
            layer_num = print_object['layer_num']

            if recorder.started and total_layers != 0 and print_job_name.endswith('.3mf'):
                print(f'{print_job_name} L: {layer_num}/{total_layers}')

        if recorder.started and core.is_not_printing_for_sure(msg):
            recorder.stop()
            print(f'File {recorder.file} finished!')
            print('Waiting patiently for next print!')
            print_job_name = None
            total_layers = None
            layer_num = None

        if not recorder.started and core.is_printing_for_sure(msg):
            recorder.start()
            print(f'Opening {recorder.file} file')

async def main(args: argparse.Namespace):
    with Recorder(args.camera_source) as r, \
        await core.mqtt_channel.open(core.bambu_mqtt_credentials.parse(args)) as ch:

        try:
            await handle(r, ch)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print('Stopping...')
    print('Bye!')

bootstrapper = Bootstrapper('Creates records from an external IP camera using the RT(S)P protocol. Recording begins when printing starts and ends when printing stops or completes.')
bootstrapper.add_argument('-s', '--camera-source', "Camera source. Eg. 'rtp://192.168.1.1' or 'rtsp://user:password@192.168.1.1/stream1'")
bootstrapper.run(main)
