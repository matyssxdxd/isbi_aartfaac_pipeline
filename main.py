import argparse
import json

from generate_run_cmd import generate_run_cmds

from visibility_html_plots import VisibiltyHTMLPlots

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--control", help="Control file")

    args = parser.parse_args()

    ctrl = json.load(open(args.control, 'r'))

    run_cmds = generate_run_cmds(ctrl)

    # Run each cmd

    for run_cmd in run_cmds:
        print(run_cmd)

    corr_files = []
    for scan in ctrl["scans"]:
        corr_file_path = f"{ctrl['output-path']}{ctrl['observation']}/{scan['scan']}/corr_files/"
        for subband in range(1, 9):
            corr_files.append(f"{corr_file_path}{scan['scan']}_{subband}.out")

    vis = VisibilityHTMLPlots(ctrl)
    vis.process_visibilities(corr_files)
    # Now process the output
