from vex import Vex
from bitstream import *

class VexReader:
    def __init__(self, file_path):
        if file_path is None:
            raise Exception('Vex file path must be provided!')

        self.vex_path = file_path
        self.vex_file = Vex(self.vex_path)


    def start_time(self, scan_nr):
        return self.vex_file["SCHED"][scan_nr.capitalize()]["start"]

    def sample_rate(self):
        dict_key = list(self.vex_file["MODE"].keys())[0]
        freq = self.vex_file["MODE"][dict_key]["FREQ"][0]
        sample_rate = str(int(float(self.vex_file["FREQ"][freq]["sample_rate"].split()[0]) * 1e+6))

        return sample_rate

    def observation_length(self, scan_nr):
        return int(self.vex_file["SCHED"][scan_nr]["station"][2].split()[0])

    def nr_subbands(self):
        dict_key = list(self.vex_file["MODE"].keys())[0]

        return self.vex_file["MODE"][dict_key]["BBC"][0].removesuffix("BBCs")

    def generate_threads_block(self):
        bitstreams, threads, modes = create_bitstreams_and_threads_block(self.vex_path)

        file = open(self.vex_path, 'a')
        file.write("*------------------------------------------------------------------------------")
        file.write(threads[0])
        file.close()

        self.vex_file = Vex(self.vex_path)

    def channel_mapping(self):
        if not "THREADS" in self.vex_file:
            self.generate_threads_block()

        threads = self.vex_file["THREADS"]["IrIbThreads#0"].getall("channel")
        mapped_idx = [0 for _ in range(len(threads))]

        for i in range(len(threads)):
            thread = threads[i]
            mapped_idx[i] = int(thread[-1])

        return " ".join(str(x) for x in mapped_idx)

    def center_frequencies(self):
        dict_key = list(self.vex_file["FREQ"].keys())[0]
        center_frequencies = []

        for i in range(0, len(self.vex_file["FREQ"][dict_key].getall("chan_def")), 2):
            center_frequencies.append(float(self.vex_file["FREQ"][dict_key].getall("chan_def")[i][1].split()[0]))

        return center_frequencies

    def site_geocentric_position(self, site_name):
        return [float(pos.split()[0]) for pos in self.vex_file["SITE"][site_name]["site_position"]]

    def source_name(self, scan_nr):
        return self.vex_file["SCHED"][scan_nr]["source"]

    def source_ra(self, source_name):
        return self.vex_file["SOURCE"][source_name]["ra"]

    def source_dec(self, source_name):
        return self.vex_file["SOURCE"][source_name]["dec"]
