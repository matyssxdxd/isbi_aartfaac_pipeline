import os
import time
import re

from vex import Vex
from dbbc_patching import patching

os.environ['TZ'] = 'UTC'
time.tzset()


def get_indexies_in_sorted_list(lst):
    y = sorted(lst)
    y1 = [y.index(i) for i in lst]
    return y1


def get_mode(vex):
    sched = vex['SCHED']
    scan = next(iter(sched))  # Python 3 way to get first key
    return sched[scan]['mode']


def get_modes(vex):
    modesList = []
    sched = vex['SCHED']
    for scan in sched:
        mode = sched[scan]['mode']
        if mode not in modesList:
            modesList.append(mode)
    return modesList


def get_stations(vex):
    return list(vex["STATION"].keys())


def get_stations_type(vex, stations):
    result = {}
    for station in stations:
        das_for_station = vex["STATION"][station]["DAS"]
        record_transport_type = vex["DAS"][das_for_station]["record_transport_type"]
        type = "THREADS" if record_transport_type in ["None", "Mark5C"] else "BITSTREAMS"
        result[station] = type
    return result


def get_channels_for_station(vex):
    channels_for_station = {}
    mode = get_mode(vex)
    freq = [i[0] for i in vex['MODE'][mode].getall('FREQ')]
    stations = [i[1:] for i in vex['MODE'][mode].getall('FREQ')]
    channels = []

    for j in range(len(freq)):
        ch = []
        for chan_def in vex['FREQ'][freq[j]].getall('chan_def'):
            ch.append(chan_def[4])
        channels.append(ch)

    for station_group in range(len(stations)):
        for s in stations[station_group]:
            channels_for_station[s] = channels[station_group]

    return channels_for_station


def get_mode_per_station(vex, modes, stations):
    result = {}
    for mode in modes:
        FREQs = vex['MODE'][mode].getall("FREQ")
        IFs = vex['MODE'][mode].getall("IF")
        BBCs = vex['MODE'][mode].getall("BBC")
        result[mode] = {}

        for station in stations:
            result[mode][station] = {}
            for freq in FREQs:
                for f in range(1, len(freq)):
                    if freq[f] == station:
                        result[mode][station]["FREQ"] = freq[0]

            for IF in IFs:
                for I in range(1, len(IF)):
                    if IF[I] == station:
                        result[mode][station]["IF"] = IF[0]

            for BBC in BBCs:
                for B in range(1, len(BBC)):
                    if BBC[B] == station:
                        result[mode][station]["BBC"] = BBC[0]

    return result


def get_DBBC_patching_strings(vex, mode_per_station, modes, stations):
    result = {}
    for mode in modes:
        result[mode] = {}
        info = mode_per_station[mode]
        for station in stations:
            result[mode][station] = []
            for i in range(len(vex["FREQ"][info[station]["FREQ"]].getall("chan_def"))):
                BBC_channel = vex["FREQ"][info[station]["FREQ"]].getall("chan_def")[i][5]
                string = re.findall(r'-?\d+\.?\d*', BBC_channel)
                string = str(int(string[0])) + vex["FREQ"][info[station]["FREQ"]].getall("chan_def")[i][2]
                BBC_string = vex["BBC"][info[station]["BBC"]].getall("BBC_assign")
                result[mode][station].append(string)
                for j in BBC_string:
                    if j[0] == BBC_channel:
                        FREQ_channel = j[2]
                        FREQ = vex["IF"][info[station]["IF"]].getall("if_def")
                        for F in FREQ:
                            if F[0] == FREQ_channel:
                                result[mode][station].append(F[-1])

            result[mode][station] = [''.join(x) for x in zip(result[mode][station][0::2], result[mode][station][1::2])]
            tmpResults = []
            for ch in range(len(result[mode][station])):
                tmp = re.findall(r'-?\d+\.?\d*', result[mode][station][ch])
                tmp = str(int(tmp[0]))
                if result[mode][station][ch][-1] == result[mode][station][ch][-2]:
                    result[mode][station][ch] = "".join(tmp + "U")
                else:
                    result[mode][station][ch] = "".join(tmp + "L")

                tmpResults.append(result[mode][station][ch] + "S")
                tmpResults.append(result[mode][station][ch] + "M")

            result[mode][station] = tmpResults
    return result


def get_DBBC_type_per_stations(modes, stations, DBBC_patching_strings):
    result = {}

    for mode in modes:
        result[mode] = {}
        for station in stations:
            try:
                strings = DBBC_patching_strings[mode][station]

                if set(strings).issubset(patching["astro3"].keys()):
                    DBBC_type = "astro3"
                elif set(strings).issubset(patching["astro2"].keys()):
                    DBBC_type = "astro2"
                else:
                    DBBC_type = "astro"

                result[mode][station] = DBBC_type
            except KeyError as error:
                print(error)

    return result


def get_DBBC_patching_values(modes, stations, DBBC_patching_strings, DBBC_type_per_stations):
    result = {}

    for mode in modes:
        result[mode] = {}
        for station in stations:
            try:
                result[mode][station] = []
                strings = DBBC_patching_strings[mode][station]
                DBBC_type = DBBC_type_per_stations[mode][station]
                for string in strings:
                    result[mode][station].append(patching[DBBC_type][string])
            except KeyError as error:
                print(error)

    return result


def create_BITSTREAMS(DBBC_patching_values, stations, channels_for_station, modes):
    bitstreams = {}
    map_of_bitstreams_and_mode = {}

    for mode in modes:
        bitstreams[mode] = {}
        for station in stations:
            if DBBC_patching_values[mode][station] not in [item[0] for item in bitstreams[mode].values()]:
                bitstreams[mode][station] = [DBBC_patching_values[mode][station],
                                             get_indexies_in_sorted_list(DBBC_patching_values[mode][station])]
            else:
                for key, value in list(bitstreams[mode].items()):
                    if value[0] == DBBC_patching_values[mode][station]:
                        k = key + station
                        del bitstreams[mode][key]
                        bitstreams[mode][k] = [DBBC_patching_values[mode][station],
                                               get_indexies_in_sorted_list(DBBC_patching_values[mode][station])]

    BITSTREAMS_block = "*\n$BITSTREAMS; \n*\n"
    mode_Nr = 0

    for mode in bitstreams:
        map_of_bitstreams_and_mode[mode] = []
        for title in bitstreams[mode]:
            VALUES = bitstreams[mode][title][0]
            INDEXIES = bitstreams[mode][title][1]

            BITSTREAMS_block += f"def {title}Btstrm#{mode_Nr};\n"
            s = list(zip(*[title[i::2] for i in range(2)]))
            a = [''.join(t) for t in s]
            s1 = ":".join(a)
            map_of_bitstreams_and_mode[mode].append([f'{title}Btstrm#{mode_Nr}', s1])
            BITSTREAMS_block += f"*  Stations = {s1}\n"

            for ch in range(len(VALUES)):
                CH = round((float(ch) + 1) / 2)
                CH = str(int(CH)).zfill(2)

                bit = "sign" if ch % 2 == 0 else "mag"

                BITSTREAMS_block += f"  stream_def = &CH{CH} : {bit} : {VALUES[ch]} : {INDEXIES[ch]};\n"
            BITSTREAMS_block += "enddef;\n*\n"

        mode_Nr += 1

    return (BITSTREAMS_block, map_of_bitstreams_and_mode)


def create_THREADS(vex, DBBC_patching_values, stations, modes):
    # works only for single threads stations
    map_of_thread_and_mode = {}
    threads = {}

    for mode in modes:
        threads[mode] = {}

        for station in stations:
            indexies = get_indexies_in_sorted_list(DBBC_patching_values[mode][station])
            indexies_THREADS = indexies[::2]
            indexies_THREADS = get_indexies_in_sorted_list(indexies_THREADS)

            if indexies_THREADS not in threads[mode].values():
                threads[mode][station] = indexies_THREADS
            else:
                for key, value in list(threads[mode].items()):
                    if value == indexies_THREADS:
                        k = key + station
                        del threads[mode][key]
                        threads[mode][k] = indexies_THREADS

    THREADS_block = "*\n$THREADS; \n*\n"

    mode_Nr = 0
    for mode in threads:
        map_of_thread_and_mode[mode] = []
        station_keys = list(threads[mode].keys())
        for title in range(len(station_keys)):
            TITLE = f"{station_keys[title]}Threads#{mode_Nr}"
            THREADS_block += f"def {TITLE};\n"
            s = list(zip(*[station_keys[title][i::2] for i in range(2)]))
            a = [''.join(t) for t in s]
            s1 = ":".join(a)
            freq = vex["MODE"][mode].getall("FREQ")
            map_of_thread_and_mode[mode].append([TITLE, s1])
            for f in freq:
                if a[0] in f[1:]:
                    data_rate = str(
                        int(float(re.findall(r'-?\d+\.?\d*', vex["FREQ"][f[0]]["sample_rate"])[0]) * 2 * len(
                            threads[mode][station_keys[title]])))  # (2bits/sample)

            THREADS_block += f"*  Stations = {s1}\n"
            THREADS_block += f"format = VDIF : : {data_rate};\n"
            THREADS_block += f"thread = 0 : 1 : 1 : {data_rate} : {len(threads[mode][station_keys[title]])} : 2 : : : 8000;\n"
            for ch in threads[mode][station_keys[title]]:
                CH = str(threads[mode][station_keys[title]].index(ch) + 1).zfill(2)
                THREADS_block += f"  channel = &CH{CH} : 0 : {ch};\n"
            THREADS_block += "enddef;\n*\n"

        mode_Nr += 1

    return (THREADS_block, map_of_thread_and_mode)


def create_bitstreams_and_threads_block(vexFile):
    vex = Vex(vexFile)
    modes = get_modes(vex)
    stations = get_stations(vex)
    stations_type = get_stations_type(vex, stations)
    BITSTREAMS_stations = [s for s in stations if stations_type[s] == "BITSTREAMS"]
    THREADS_stations = [s for s in stations if stations_type[s] == "THREADS"]
    channels_for_station = get_channels_for_station(vex)
    mode_per_station = get_mode_per_station(vex, modes, stations)
    DBBC_patching_strings = get_DBBC_patching_strings(vex, mode_per_station, modes, stations)
    DBBC_type_per_stations = get_DBBC_type_per_stations(modes, stations, DBBC_patching_strings)
    DBBC_patching_values = get_DBBC_patching_values(modes, stations, DBBC_patching_strings, DBBC_type_per_stations)
    BITSTREAMS = create_BITSTREAMS(DBBC_patching_values, BITSTREAMS_stations, channels_for_station, modes)
    THREADS = create_THREADS(vex, DBBC_patching_values, THREADS_stations, modes)

    return (BITSTREAMS, THREADS, modes)