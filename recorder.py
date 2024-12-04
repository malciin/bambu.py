import signal
import subprocess
import shlex
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

def create(source: str) -> Recorder:
    return Recorder(source)
