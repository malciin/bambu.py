import asyncio
import secret
import utilities
import recorder
import mqtt_channel

async def main():
    recorder_instance: recorder.Recorder = None
    print_job_name: str = None
    layer_num = 0
    total_layers = 0
    channel = await mqtt_channel.open()

    async for msg in channel:
        if 'info' in msg: continue
        if 'system' in msg: continue
        if 'liveview' in msg: continue
        if 'print' not in msg:
            print('Unhandled json:', msg)
            continue

        print_object = msg['print']
        gcode_state = utilities.get_or_none(print_object, 'gcode_state')
        should_start = ('mc_print_line_number' in print_object and gcode_state == None) or gcode_state == 'PREPARE' or gcode_state == 'RUNNING'
        should_end = gcode_state == 'FINISH' or gcode_state == 'FAILED' or (utilities.get_or_none(print_object, 'command') == 'stop' and utilities.get_or_none(print_object, 'result') == 'success')

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
            recorder_instance = recorder.create(secret.RTSP)
            print(f'Opening {recorder_instance.file} file')

asyncio.run(main())