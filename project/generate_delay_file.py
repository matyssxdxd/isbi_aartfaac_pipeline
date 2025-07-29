import struct

from pycalc11 import Calc
from astropy import coordinates as ac
from astropy import units as un
from astropy.time import Time

from utils.VexReader import VexReader
from datetime import datetime, timedelta


def generate_delay_file(scan, ctrl):
    vex = VexReader(ctrl["vex_path"])

    irbene = vex.site_geocentric_position("IRBENE")
    irbene16 = vex.site_geocentric_position("IRBENE16")

    irbene_loc = ac.EarthLocation.from_geocentric(irbene[0] * un.m, irbene[1] * un.m, irbene[2] * un.m)
    irbene16_loc = ac.EarthLocation.from_geocentric(irbene16[0] * un.m, irbene16[1] * un.m, irbene16[2] * un.m)

    if ctrl["reference_station"] == "Ib":
        site_locs = [irbene_loc, irbene16_loc]
        site_names = ["IRBENE", "IRBENE16"]
    else:
        site_locs = [irbene16_loc, irbene_loc]
        site_names = ["IRBENE16", "IRBENE"]

    source = vex.source_name(scan)
    source_ra = vex.source_ra(source)
    source_dec = vex.source_dec(source)

    source_coords = ac.SkyCoord([source_ra], [source_dec], frame="fk5", equinox="J2000.0")

    start_time = vex.start_time(scan)

    year = int(start_time[:4])
    day_of_year = int(start_time[5:8])
    hour = int(start_time[9:11])
    minute = int(start_time[12:14])
    second = int(start_time[15:17])

    date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)

    formatted_date = date.strftime(f"%Y-%m-%dT{hour:02}:{minute:02}:{second:02}.000")
    start_time = Time(formatted_date, format="isot", scale='utc')

    duration = int(vex.observation_length(scan) / 60)

    ci = Calc(
        station_names=site_names,
        station_coords=site_locs,
        source_coords=source_coords,
        start_time=start_time,
        duration_min=duration
    )
    ci.run_driver()

    print(ci.delay)
    true_delays = [[], []]
    frac_delays = [[], []]
    ns_per_unit = 62.5

    for delay_entry in ci.delay:
        val1 = delay_entry[0][0][0].to_value(un.ns)
        val2 = delay_entry[0][1][0].to_value(un.ns)

        x = val1 - val2
        true_delay_ns = round(x / ns_per_unit)
        frac_delay_ns = x - true_delay_ns * ns_per_unit

        true_delays[1].append(true_delay_ns)
        frac_delays[1].append(frac_delay_ns * 1e-9)

        true_delays[0].append(0)
        frac_delays[0].append(0)

    print(true_delays)
    print(frac_delays)
    center_frequencies = vex.center_frequencies()
    print(center_frequencies)

    num_rows = len(true_delays)
    num_cols = len(true_delays[0])

    # with open(f"{ctrl['output-path']}{ctrl['observation']}/{scan}/delays.bin", "wb") as file:
    #     file.write(struct.pack("II", num_rows, num_cols))

    #     for row in true_delays:
    #         file.write(struct.pack("i" * num_cols, *row))

    #     for row in frac_delays:
    #         file.write(struct.pack("d" * num_cols, *row))

    #     file.write(struct.pack("i", len(center_frequencies)))
    #     file.write(struct.pack("d" * len(center_frequencies), *center_frequencies))
