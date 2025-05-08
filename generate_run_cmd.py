import os

from VexReader import VexReader
from generate_delay_file import generate_delay_file
from datetime import datetime, timedelta

def generate_run_cmds(ctrl):
    run_cmds = []
    vex = VexReader(ctrl["vex-path"])
    scans = ctrl["scans"]
    subbands = len(ctrl["correlation-channels"])
    nr_chan_per_subband = ctrl["number_of_channels_per_subband"]
    sample_rate = vex.sample_rate()
    channel_mapping = vex.channel_mapping()
    output_path = f"{ctrl['output-path']}{ctrl['observation']}/"

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for scan in scans:
        run_cmds.append(generate_run_cmd(scan, vex, channel_mapping, nr_chan_per_subband, subbands, sample_rate, output_path, ctrl["reference-station"]))
        generate_delay_file(scan["scan"] ,ctrl)

    return run_cmds

def generate_run_cmd(scan, vex, channel_mapping, number_of_channels_per_subband, subbands, sample_rate, output_path, reference_station):
    if reference_station == "Ib":
        input_files = f"{scan['file-path-ib']},{scan['file-path-ir']}"
    else:
        input_files = f"{scan['file-path-ir']},{scan['file-path-ib']}"

    input_str = vex.start_time(scan["scan"])

    year = int(input_str[0:4])
    day_of_year = int(input_str[5:8])
    hour = int(input_str[9:11])
    minute = int(input_str[12:14])
    second = int(input_str[15:17])

    # Convert day of year to date
    date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1, hours=hour, minutes=minute, seconds=second)

    # Format to desired output
    start_time = date.strftime('%Y-%m-%d %H:%M:%S')

    runtime = scan["runtime"] # Need to verify that runtime is correct

    output = f"{output_path}{scan['scan']}/corr_files/"

    if not os.path.exists(output):
        os.makedirs(output)

    for subband in range(1, subbands + 1):
        output += f"{scan['scan']}_{subband}.out"
        if subband <= subbands - 1:
            output += ","

    return f"TZ=UTC ISBI/ISBI -M {channel_mapping} -K {output_path}{scan['scan']}/delays.bin -p1 -n2 -t12512 -c{number_of_channels_per_subband} -C{number_of_channels_per_subband - 1} -b16 -s{subbands} -m15 -D {start_time} -r{runtime} -g0 -q1 -R0 -B0 -f{sample_rate} -i {input_files} -o {output}"
