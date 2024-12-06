from core.utilities import get_or_none

def is_printing_for_sure(mqtt_msg: any):
    print_object = mqtt_msg['print']
    gcode_state = get_or_none(print_object, 'gcode_state')
    
    return ('mc_print_line_number' in print_object and gcode_state == None) or gcode_state == 'PREPARE' or gcode_state == 'RUNNING'

def is_not_printing_for_sure(mqtt_msg: any):
    print_object = mqtt_msg['print']
    gcode_state = get_or_none(print_object, 'gcode_state')
    
    return gcode_state == 'FINISH' or gcode_state == 'FAILED' or (get_or_none(print_object, 'command') == 'stop' and get_or_none(print_object, 'result') == 'success')
