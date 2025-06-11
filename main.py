import argparse
import json
import subprocess

from generate_run_cmd import generate_run_cmds

from visibility_html_plots import VisibilityHTMLPlots

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--control", help="Control file")

    args = parser.parse_args()

    ctrl = json.load(open(args.control, 'r'))

    run_cmds = generate_run_cmds(ctrl)

    # Run each cmd

    for run_cmd in run_cmds:
        subprocess.run(run_cmd, shell=True, cwd='/mnt/VLBI/softs/Matiss_AARTFAAC/ISBI-AARTFAAC')

    corr_files = []
    for scan in ctrl["scans"]:
        corr_file_path = f"{ctrl['output-path']}{ctrl['observation']}/{scan['scan']}/corr_files/"
        for subband in range(1, 9):
            corr_files.append(f"{corr_file_path}{scan['scan']}_{subband}.out")

    vis = VisibilityHTMLPlots(ctrl, "No0002")
    vis.process_visibilities(corr_files)
    # Now process the output
