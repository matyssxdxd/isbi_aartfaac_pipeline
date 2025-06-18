import argparse
import json
import subprocess
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from config import config

from project.generate_run_cmds import generate_run_cmds


# from generate_run_cmd import generate_run_cmds

# from visibility_html_plots import VisibilityHTMLPlots

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
        for subband in range(1, len(ctrl['subbands']) + 1):
            print(f'{scan["raw_result_path"]}{scan["scan_nr"]}_{subband}.out')
    # corr_files = []
    # for scan in ctrl["scans"]:
    #     corr_file_path = f"{ctrl['output-path']}{ctrl['observation']}/{scan['scan']}/corr_files/"
    #     for subband in range(1, 9):
    #         corr_files.append(f"{corr_file_path}{scan['scan']}_{subband}.out")

    # vis = VisibilityHTMLPlots(ctrl, "No0002")
    # vis.process_visibilities(corr_files)
    # # Now process the output
    # TODO: If the code is being debugged, don't run the correlation but instead provide already correlated files.
