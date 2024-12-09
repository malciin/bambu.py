# Various QoL python scripts for your Bambu printer :)

## Setup

```bash
pip install -r requirements.txt
```

Additionaly for windows only scripts (toast notification) use:

```
pip install -r requirements.win.txt
```

## Usage

Every script have help via `--help` option. Just write `python3 XYZ.py --help`.

### `notify.py`

<img src="./resources/870n5bIcCG.png" />

<audio controls="controls">
  <source type="audio/wav" src="./resources/notification.en.wav"></source>
</audio>

Sends Windows 10/11 toast notifications when printing is complete.

Example usage:

```bash
python3 notify.py -ip 192.168.1.100 -ac 21xxxxxx -sn 03xxxxxxxxxxxxx
```

### `recorder.py`

https://github.com/user-attachments/assets/c02920be-87f0-40e6-bcae-b0e910b8f983

Creates records from an **external** IP camera using the RT(S)P protocol. Recording begins when printing starts and ends when printing stops or completes.

Example usage:

```bash
python3 recorder.py -ip 192.168.1.100 -ac 21xxxxxx -sn 03xxxxxxxxxxxxx -s rtsp://user:pass@ipcam-ip/stream1
```

### `dumper.py`

Dumps every mqtt messages from printer to mqtt folder.

Example usage:

```bash
python3 notify.py -ip 192.168.1.100 -ac 21xxxxxx -sn 03xxxxxxxxxxxxx
```
