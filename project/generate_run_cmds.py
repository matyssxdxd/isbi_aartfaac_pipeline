import sys
import os

from utils.VexReader import VexReader
# from generate_delay_file import generate_delay_file
from datetime import datetime, timedelta
from config import config

def generate_run_cmds(ctrl):
    run_cmds = []
    vex = VexReader(ctrl['vex_path'])
    output_path = ctrl['output_path']
    subbands = len(ctrl['subbands'])
    
    if subbands < 1 or subbands > 8:
        sys.exit('INPUT PARAMETER ERROR: Subbands should be between 1 and 8')
    
    reference_station = ctrl['reference_station']
    
    if reference_station not in ['Ib', 'Ir']:
        sys.exit('INPUT PARAMETER ERROR: Reference station should be either Ib or Ir')
        
    nr_channels_per_subband = ctrl['nr_channels_per_subband']
    
    if not (nr_channels_per_subband > 0 and (nr_channels_per_subband & (nr_channels_per_subband - 1)) == 0):
        sys.exit('INPUT PARAMETER ERROR: Number of chanenls per subband should be a power of 2')
        
    scans = ctrl['scans']
    sample_rate = vex.sample_rate()
    channel_mapping = vex.channel_mapping()

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for scan in scans:
        run_cmds.append(generate_run_cmd(scan, vex, channel_mapping, nr_channels_per_subband, subbands, sample_rate, output_path, reference_station))
        # generate_delay_file(scan["scan"] ,ctrl)

    return run_cmds

def generate_run_cmd(scan, vex, channel_mapping, number_of_channels_per_subband, subbands, sample_rate, output_path, reference_station):
    file_path_ib = scan['file_ib']
    file_path_ir = scan['file_ir']
    
    if (not os.path.isfile(file_path_ib) or not os.path.isfile(file_path_ir)) and not config.DEBUG:
        sys.exit(f'{scan["scan_nr"].upper()} INPUT PARAMETER ERROR: One or both of the input files do not exist')
        
    if reference_station == 'Ib':
        input_files = f'{file_path_ib},{file_path_ir}'
    else:
        input_files = f'{file_path_ir},{file_path_ib}'

    date_str = vex.start_time(scan['scan_nr'])

    year = int(date_str[0:4])
    day_of_year = int(date_str[5:8])
    hour = int(date_str[9:11])
    minute = int(date_str[12:14])
    second = int(date_str[15:17])

    date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1, hours=hour, minutes=minute, seconds=second)

    start_time = date.strftime('%Y-%m-%d %H:%M:%S')

    runtime = scan['runtime']
    
    if runtime > vex.observation_length(scan['scan_nr']) or runtime < 1:
        sys.exit(f'{scan["scan_nr"].upper()} INPUT PARAMETER ERROR: Runtime should not be less than 1 or larger that the actual scan\'s observation length')

    output = scan['raw_result_path']

    if not os.path.exists(output):
        os.makedirs(output)

    output_files = ""
    for subband in range(1, subbands + 1):
        output_files += f"{output}{scan['scan_nr']}_{subband}.out"
        if subband <= subbands - 1:
            output_files += ","

    return f'TZ=UTC ISBI/ISBI -M {channel_mapping} -K {output_path}/{scan["scan_nr"]}/delays.bin -p1 -n2 -t12512 -c{number_of_channels_per_subband} -C{number_of_channels_per_subband - 1} -b16 -s{subbands} -m15 -D \'{start_time}\' -r{runtime} -g0 -q1 -R0 -B0 -f{sample_rate} -i {input_files} -o {output_files}'
