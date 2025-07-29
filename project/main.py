import subprocess
import argparse
import json
import sys

from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from project.generate_run_cmds import generate_run_cmds
from project.generate_plots import generate_plots
from project.process_data import process_data
from project.generate_delay_file import generate_delay_file
from config import config

if __name__ == '__main__':
    # TODO: Develop a UI that lets User provide a VEX file path and that runs the
    #       generate_control_file.py script. Then allow user to edit the control file
    #       to provide VDIF file paths and change other config. After everything is
    #       edited, let User run the AARTFAAC correlator using the control file.
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--ctrl', help='Control file')

    args = parser.parse_args()
    ctrl_path = args.ctrl

    with open(ctrl_path, 'r') as ctrl_file:
        ctrl = json.load(ctrl_file)

    run_cmds = generate_run_cmds(ctrl)

    for cmd in run_cmds:
        if config.DEBUG:
            print(cmd)
        else:
            subprocess.run(cmd, shell=True, cwd=config.AARTFAAC_PATH)

    for scan in ctrl['scans']:
        corr_files = []
        for subband in range(1, len(ctrl['subbands']) + 1):
            corr_files.append(
                f'{scan["raw_result_path"]}{scan["scan_nr"]}_{subband}.out')
        # TODO: Right now it is being returned as an array, but it should first be saved in a specific format
        processed_data = process_data(scan, corr_files, ctrl['output_path'])
        generate_plots(processed_data, scan, ctrl['output_path'])
