import argparse
import json
import os
import struct
import gc
import sys
from multiprocessing.synchronize import RLock

import numpy as np
from matplotlib import pyplot as plt

from vex import Vex

class Header:
    def __init__(self):
        self.magic = None
        self.nr_receivers = None
        self.nr_polarizations = None
        self.correlation_mode = None
        self.start_time = None
        self.end_time = None
        self.weights = None
        self.nr_samples_per_integration = None
        self.nr_channels = None
        self.pad0 = None
        self.first_channel_frequency = None
        self.channel_bandwidth = None
        self.pad1 = None

    def print_header(self):
        print("Header contents:")
        for key, value in vars(self).items():
            print(f"{key}: {value}")

class VisibilityHTMLPlots:

    def __init__(self, control):
        self.control = control 
        self.vex = Vex(self.control['vex-path'])
        self.nr_subbands = len(self.control['correlation-channels'])
        self.nr_receivers = 3
        self.nr_channels = self.control['number_of_channels_per_subband'] - 1
        self.nr_polarizations = 4
        self.visibilities = []
        self.freq_block = None

    def read_visibility_file(self, visibility_path):
        headers = []
        visibilities = []

        with open(visibility_path, 'rb') as file:
            while True:
                try:
                    # Read header
                    header = Header()
                    header.magic = struct.unpack('I', file.read(4))[0]
                    header.nr_receivers = struct.unpack('H', file.read(2))[0]
                    header.nr_polarizations = struct.unpack('B', file.read(1))[0]
                    header.correlation_mode = struct.unpack('B', file.read(1))[0]
                    header.start_time = struct.unpack('d', file.read(8))[0]
                    header.end_time = struct.unpack('d', file.read(8))[0]
                    header.weights = struct.unpack('I' * 300, file.read(4 * 300))
                    header.nr_samples_per_integration = struct.unpack('I', file.read(4))[0]
                    header.nr_channels = struct.unpack('H', file.read(2))[0]
                    header.pad0 = file.read(2)
                    header.first_channel_frequency = struct.unpack('d', file.read(8))[0]
                    header.channel_bandwidth = struct.unpack('d', file.read(8))[0]
                    header.pad1 = file.read(288)

                    vis_dtype = np.complex64
                    nr_baselines = header.nr_receivers + int(header.nr_receivers * (header.nr_receivers - 1) / 2)
                    vis_shape = (nr_baselines, header.nr_channels, header.nr_polarizations)
                    vis_zeros = np.zeros(vis_shape, vis_dtype)

                    # Read visibilities
                    vis = file.read(vis_zeros.size * vis_zeros.itemsize)

                    if len(vis) < vis_zeros.size * vis_zeros.itemsize:
                        break

                    vis = np.frombuffer(vis, dtype=vis_dtype).reshape(vis_shape)
                    headers.append(header)
                    visibilities.append(vis)
                except struct.error:
                    break

        return headers, visibilities

    def average_visibilities(self, visibilities):
        averaged_visibilities = np.asarray(visibilities)
        averaged_visibilities = np.mean(averaged_visibilities, axis=0)
        averaged_visibilities = np.transpose(averaged_visibilities, (0, 2, 1))
        return averaged_visibilities

    def get_freq_block(self):
        frequency = self.vex["MODE"][list(self.vex["MODE"].keys())[0]]["FREQ"][0]
        chan_def = self.vex["FREQ"][frequency].getall("chan_def")
        result = []

        for i, chan in enumerate(chan_def):
            pol1 = "LCP"
            pols = ["LCP", "RCP"]

            if i % 2 == 0:
                pol1 = "RCP"
                pols = ["RCP", "LCP"]
            for pol2 in pols:
                center_frequency = float(chan[1].split(" ")[0])
                bandwidth = float(chan[3].split(" ")[0])
                upper = center_frequency + bandwidth
                lower = center_frequency
                bound = chan[2]

                if bound == "L":
                    lower = center_frequency - bandwidth
                    upper = center_frequency

                channel = {"freq": center_frequency,
                           "lower_freq": lower,
                           "upper_freq": upper,
                           "bound": bound,
                           "bandwidth": bandwidth,
                           "channel": int(chan[4].removeprefix("CH")),
                           "bbc": int(chan[5].removeprefix("BBC")),
                           "pol1": pol1,
                           "pol2": pol2, }

                result.append(channel)

        return result

    def generate(self, baseline):
        y_ll = []
        y_rr = []

        for i in range(len(self.visibilities)):
            y = self.visibilities[i][baseline][0]
            y_normalized = y / np.median(np.abs(y))
            y_rr.extend(y_normalized)

            y = self.visibilities[i][baseline][3]
            y_normalized = y / np.median(np.abs(y))
            y_ll.extend(y_normalized)

        x = np.arange(len(y_ll))
        plt.figure(figsize=(12, 8))
        plt.ylim(0, 2)
        plt.plot(x, y_ll, color="green")
        plt.plot(x, y_rr, color="red")
        plt.show()
        plt.close()

    def cross_correlation_amplitude_phase(self):
        fig, axs = plt.subplots(2, 1, figsize=(32, 12), sharex=True, gridspec_kw={'height_ratios': [1, 2]})
        plt.rcParams.update({'font.size': 22})
        polarizations = {0: "RR", 1: "RL", 2: "LR", 3: "LL"}
        colors = {0: "red", 1: "blue", 2: "aqua", 3: "green"}

        axs[1].set_ylim(0, 0.25 * 1e6)
        axs[1].ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        axs[1].set_ylabel("Amplitude", fontsize=22)
        axs[1].set_xlabel("Channel", fontsize=22)

        axs[0].set_ylabel("Phase (deg)", fontsize=22)

        for polarization in range(self.nr_polarizations):
            y = []
            phase_y = []
            for subband in range(self.nr_subbands):
                amplitude = self.visibilities[subband][1][polarization]
                phase = self.visibilities[subband][1][polarization]
                y.extend(amplitude)
                phase_y.extend(phase)

            x = np.arange(len(y))
            x_phase = np.arange(len(phase_y))

            axs[0].scatter(x_phase, np.angle(phase_y, deg=True), label=f"Phase {polarizations[polarization]}", color=colors[polarization], s=25)
            axs[1].plot(x, np.abs(y), label=f"Amplitude {polarizations[polarization]}", color=colors[polarization])

        axs[0].legend()
        axs[1].legend()
        plt.tight_layout()
        plt.show()
        plt.close()

    def save_plot(self, x, y, title, xlabel, ylabel, filename, plot_dir):
        plt.figure(figsize=(12, 8))

        # Make the line thinner by setting a smaller linewidth
        plt.plot(x, y, label=title, color='purple', linewidth=0.8)

        plt.title(title, fontsize=18)

        # Use plain formatting for y-axis instead of scientific notation
        plt.ticklabel_format(axis='y', style='plain')

        # Add grid lines to match the reference image
        plt.grid(True, linestyle=':', alpha=0.7)

        plt.xlabel(xlabel, fontsize=16)
        plt.ylabel(ylabel, fontsize=16)

        # Set axis limits similar to the reference image if needed
        # plt.xlim(min(x), max(x))
        # plt.ylim(0, max(y) * 1.1)

        plt.tight_layout()

        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)

        plt.savefig(os.path.join(plot_dir, filename), dpi=300)
        plt.close()

    def process_visibilities(self, visibility_files):
        for visibility_file in visibility_files:
            headers, visibilities = self.read_visibility_file(visibility_file)
            # num_polarizations = len(visibilities[1][1][0])
            # num_channels = len(visibilities[1][1])
            # x = np.arange(num_channels)
            #
            # for pol in range(num_polarizations):
            #     plt.figure(figsize=(12, 8))
            #     y = [visibilities[1][1][i][pol] for i in range(num_channels)]
            #     y_ampl = np.abs(y)
            #     plt.plot(x, y_ampl, label=f'Polarization {pol}', color='deepskyblue')
            #     plt.xlabel('Channel')
            #     plt.ylabel('Amplitude')
            #     plt.title(f'Polarization {pol}')
            #     plt.legend()
            #     plt.tight_layout()
            #     plt.show()
            self.visibilities.append(self.average_visibilities(visibilities))
        # self.cross_correlation_amplitude_phase()
        self.freq_block = self.get_freq_block()
        subband = 0

        plt.rcParams.update({'font.size': 16, 'lines.linewidth': 2, 'axes.grid': True})

        html = open("./index.html", "w")
        html.write("<!DOCTYPE html>")
        html.write("<html lang=\"en\"")
        html.write("<head>")
        html.write("<meta charset=\"UTF-8\">")
        html.write("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        html.write("<title>Visibilities</title>")
        html.write("<style>")
        html.write("""
                .visibility { 
                    display: flex; 
                    align-items: center; 
                    width: 100%; 
                    gap: 10px; 
                }
                .image-link {
                    position: relative;
                }
                .image-link img {
                    display: none;
                    position: absolute;
                    top: 0;
                    left: 100%;
                    max-width: 200px;
                    max-height: 200px;
                    margin-left: 10px;
                    z-index: 10;
                }
                .image-link:hover img {
                    display: block;
                }
                table, th, td, tr {
                    border: 1px solid black;
                    border-collapse: collapse;
                    padding: 10px;
                }
                """)
        html.write("</style>")
        html.write("</head>")
        html.write("<body>")
        html.write("<table>")
        html.write("<tr>"
                   f"<th rowspan=\"2\">{list(self.vex['EXPER'].keys())[0]}</th>"
                   "<th colspan=\"2\">Auto correlations (BBC number)</th>"
                   "<th colspan=\"3\">Cross correlations</th>"
                   "<th rowspan=\"2\">Offset</th>"
                   "<th rowspan=\"2\">SNR</th>"
                   "</tr>"
                   "<tr>"
                   "<th>Ib</th>"
                   "<th>Ir</th>"
                   "<th colspan=\"3\">Ib-Ir</th>"
                   "</tr>")

        for i, freq in enumerate(self.freq_block):
            if i != 0 and i % 4 == 0:
                subband += 1

            polarizations = {"RCP-RCP": 0, "RCP-LCP": 1, "LCP-RCP": 2, "LCP-LCP": 3}
            baselines = {0: "Ib", 1: "IbIr", 2: "Ir"}
            current_polarization = polarizations[f"{freq['pol1']}-{freq['pol2']}"]
            filename = f"{subband}_{freq['freq']}{freq['bound']}_"

            html.write("<tr>")
            html.write(f"<th>{freq['freq']}MHz, {freq['bound']}, {freq['pol1']}-{freq['pol2']}</th>")

            # Plot auto correlation
            if current_polarization in [0, 3]:
                for baseline in [0, 2]:
                    image_directory = "./out/plots/auto_correlations/"
                    file = f"{filename}{baselines[baseline]}_{current_polarization}.png"
                    y = np.abs(self.visibilities[subband][baseline][current_polarization])
                    y_normalized = y / np.median(np.abs(y)) * 100
                    x = np.linspace(freq['lower_freq'], freq['upper_freq'], len(y))
                    self.save_plot(x, y_normalized, f"{baselines[baseline]}",
                              "Frequency (MHz)", "Amplitude",
                              file,
                              image_directory)
                    html.write(
                        f"<th class=\"image-link\"><a href=\"{image_directory}{file}\">{freq['bbc']}</a>")
                    html.write(
                        f"<img src=\"{image_directory}{filename}{baselines[baseline]}_{current_polarization}.png\" alt=\"Image\">")
                    html.write("</th>")
            else:
                html.write("<th colspan=\"2\">Cross hands</th>")

            # Plot cross correlations
            y = self.visibilities[subband][1][current_polarization]
            x = np.linspace(freq['lower_freq'], freq['upper_freq'], len(y))
            amplitude = np.abs(y)
            phase = np.angle(y, deg=True)
            lag_y = abs(np.fft.fftshift(np.fft.irfft(y)))
            lag = lag_y.argmax() - 450 + 1
            # offset = 1. - abs(lag) / float(450 - 1) if (lag < 450 - 1) else 1.
            dict_key = list(self.vex["MODE"].keys())[0]
            freq = self.vex["MODE"][dict_key]["FREQ"][0]
            # sample_rate = int(float(self.vex["FREQ"][freq]["sample_rate"].split()[0]) * 1e+6)
            # ap = np.median(np.abs(y))**2
            # noise = np.sqrt(ap) / (2 * 0.881 * np.sqrt(sample_rate * 180 * offset))
            # snr = lag_y.max() / noise
            ap = 0
            noise = 0
            snr = 0
            offset = 0

            # Amplitude Plot
            self.save_plot(x, amplitude, f"Amplitude {baselines[1]}",
                      "Frequency (MHz)", "Amplitude", f"{filename}{baselines[1]}_amplitude_{current_polarization}.png",
                      "./out/plots/cross_correlations/amplitude/")

            # Phase Plot
            self.save_plot(x, phase, f"Phase {baselines[1]}",
                      "Frequency (MHz)", "Phase", f"{filename}{baselines[1]}_phase_{current_polarization}.png",
                      "./out/plots/cross_correlations/phase/")

            # Lag Plot
            lag_x = np.arange(-(self.nr_channels - 1), self.nr_channels - 1)
            self.save_plot(lag_x, lag_y, f"Lag {baselines[1]}",
                      "Lag", "Amplitude", f"{filename}{baselines[1]}_lag_{current_polarization}.png",
                      "./out/plots/cross_correlations/lag/")

            image_directory = "./out/plots/cross_correlations/lag/"
            html.write("<th class=\"image-link\">")
            html.write(f"<a href=\"{image_directory}{filename}{baselines[1]}_lag_{current_polarization}.png\">lag </a>")
            html.write(
                f"<img src=\"{image_directory}{filename}{baselines[1]}_lag_{current_polarization}.png\" alt=\"Image\">")
            html.write("</th>")

            image_directory = "./out/plots/cross_correlations/amplitude/"
            html.write("<th class=\"image-link\">")
            html.write(
                f"<a href=\"{image_directory}{filename}{baselines[1]}_amplitude_{current_polarization}.png\">amplitude </a>")
            html.write(
                f"<img src=\"{image_directory}{filename}{baselines[1]}_amplitude_{current_polarization}.png\" alt=\"Image\">")
            html.write("</th>")

            image_directory = "./out/plots/cross_correlations/phase/"
            html.write("<th class=\"image-link\">")
            html.write(
                f"<a href=\"{image_directory}{filename}{baselines[1]}_phase_{current_polarization}.png\">phase </a>")
            html.write(
                f"<img src=\"{image_directory}{filename}{baselines[1]}_phase_{current_polarization}.png\" alt=\"Image\">")
            html.write("</th>")

            html.write("<th style=\"font-size:12px\">")
            html.write(f"{offset}")
            html.write("</th>")

            html.write("<th style=\"font-size:12px\">")
            html.write(f"{snr}")
            html.write("</th>")

            html.write("</tr>")

        html.write("</table>")
        html.write("</body>")
        html.write("</html>")
        html.close()
