import argparse
import json
import sys
import os

from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from config import config
from utils.VexReader import VexReader

def generate_control_file(vex_path):
    vex = VexReader(vex_path)
    scans = vex.get_scans()

    control_file = {}
    control_file['observation'] = vex.get_observation()
    control_file['vex_path'] = os.path.abspath(vex_path)
    control_file['output_path'] = config.OUTPUT_PATH + '/' +vex.get_observation()
    control_file['subbands'] = [1, 2, 3, 4, 5, 6, 7, 8]
    control_file['reference_station'] = "Ib"
    control_file['nr_channels_per_subband'] = 128
    control_file['scans'] = []

    for scan in scans:
        raw_result_path = control_file['output_path'] + '/' + scan + '/' + 'corr_files/'
        
        if not os.path.exists(raw_result_path):
            os.makedirs(raw_result_path)
        
        control_file['scans'].append({
            'scan_nr': scan,
            'file_ir': '',
            'file_ib': '',
            'runtime': vex.observation_length(scan),
            'raw_result_path': raw_result_path
        })

    output_path = config.OUTPUT_PATH + '/' + control_file['observation']

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    with open(output_path + '/ctrl.json', 'w') as output:
        json.dump(control_file, output, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vex', help='Observations VEX file')

    args = parser.parse_args()
    vex_path = args.vex

    generate_control_file(vex_path)
