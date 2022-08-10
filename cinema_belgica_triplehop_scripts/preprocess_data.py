import csv
import datetime
import json
import os
import re
import shutil
import time
import typing

import edtf
import typer

RE_SIMPLE_YEAR = re.compile(r"^[0-9]{4}$")
RE_SIMPLE_INTERVAL = re.compile(r"^[0-9]{4}[/][0-9]{4}$")
RE_MEMBERS = re.compile(r"^[{][0-9]{4}[0-9,. ]+[}]$")


def fix_cell(value: str, short_config: typing.Dict):
    if value in ["", "N/A", "n/a"]:
        return ""
    if short_config is None:
        return value

    if "nullable" in short_config:
        if value in short_config["nullable"]:
            return ""
    if "list" in short_config:
        delimiter = short_config["list"]
        return delimiter.join(
            [
                v.strip()
                for v in value.split(delimiter)
                if v.strip() not in ["", "N/A", "n/a"]
            ]
        )
    if "venue_date" in short_config:
        m = re.match(r"^([0-9]{3})(?:[?]|X[?])$", value)
        if m:
            return f"{m.group(1)}X"
        if value == "*":
            return ".."
        if value == "1967-1968?":
            return "[1967,1968]"
        if value == "1935/36":
            return "[1935,1936]"
        if value == "1962/68":
            return "[1963..1968]"
    if "screen_interval" in short_config:
        value = value.replace("1935/36", "1935~")
        value = value.replace("N/A", "")
        return value.replace("-", "/").replace("*?", "..").replace("*", "..")
    if "seat_interval" in short_config:
        if "," in value:
            # set representation
            return f'{{{value.replace("-", "..")}}}'
        return value.replace("-", "/")
    return value


def fix_data(filename: str, config: typing.Dict):
    with open(f"data/original/{filename}") as input_file, open(
        f"data/clean/{filename}", "w"
    ) as output_file:
        input_reader = csv.reader(input_file)
        output_writer = csv.writer(output_file, lineterminator="\n")

        header = next(input_reader)
        output_writer.writerow(header)

        short_config = []
        for h in header:
            if h in config:
                short_config.append(config[h])
            else:
                short_config.append(None)

        for row in input_reader:
            output_writer.writerow(
                [fix_cell(c, short_config[i]) for (i, c) in enumerate(row)]
            )


configs = {
    "tblFilm.csv": {
        "country": {
            "list": "|",
        },
    },
    "tblAddress.csv": {
        "city_name": {
            "nullable": ["?"],
        },
        "postal_code": {
            "nullable": ["?", "NA"],
        },
    },
    "tblVenue.csv": {
        "date_opened": {
            "nullable": ["NA?"],
            "venue_date": None,
        },
        "date_closed": {
            "nullable": ["NA?"],
            "venue_date": None,
        },
    },
    "tblVenueScreen.csv": {
        "years": {
            "screen_interval": None,
        },
    },
    "tblVenueSeats.csv": {
        "years": {
            "seat_interval": None,
        },
    },
    "datasets/09_2.csv": {
        "Brondatum": {
            "nullable": ["n/a!"],
        },
    },
}


def main(action: typing.List[str] = typer.Option(None)):
    if not action or "remove" in action:
        dirs = ["data/clean", "data/processed"]
        for d in dirs:
            files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
            if d == "data/clean":
                for f in os.listdir(f"{d}/source_links"):
                    if os.path.isfile(f"{d}/source_links/{f}"):
                        files.append(f"source_links/{f}")
                for f in os.listdir(f"{d}/datasets"):
                    if os.path.isfile(f"{d}/datasets/{f}"):
                        files.append(f"datasets/{f}")
                for f in os.listdir(f"{d}/datasets/sources_input"):
                    if os.path.isfile(f"{d}/datasets/sources_input/{f}"):
                        files.append(f"datasets/sources_input/{f}")
                if os.path.isfile(os.path.join(d, "images/programmes_image_urls.csv")):
                    files.append("images/programmes_image_urls.csv")
            for f in files:
                os.remove(os.path.join(d, f))

    if not action or "clean" in action:
        files = [
            f
            for f in os.listdir("data/original")
            if os.path.isfile(f"data/original/{f}") and os.path.splitext(f)[1] == ".csv"
        ]
        files.extend(
            [
                f"source_links/{f}"
                for f in os.listdir("data/original/source_links")
                if os.path.isfile(f"data/original/source_links/{f}")
                and os.path.splitext(f)[1] == ".csv"
            ]
        )
        files.extend(
            [
                f"datasets/{f}"
                for f in os.listdir("data/original/datasets")
                if os.path.isfile(f"data/original/datasets/{f}")
                and os.path.splitext(f)[1] == ".csv"
            ]
        )
        files.extend(
            [
                f"datasets/sources_input/{f}"
                for f in os.listdir("data/original/datasets/sources_input")
                if os.path.isfile(f"data/original/datasets/sources_input/{f}")
                and os.path.splitext(f)[1] == ".csv"
            ]
        )
        files.append("images/programmes_image_urls.csv")
        for filename in files:
            fix_data(filename, configs.get(filename, {}))

    if not action or "addresses" in action:
        print("Preprocessing addresses")
        # tblAddress.csv -> tblCity.csv and tblJoinAddressCity.csv
        # tblAddress -> save geodata as geojson
        city_counter = 1
        city_lookup = {}

        with open("data/clean/tblAddress.csv") as address_file, open(
            "data/processed/tblCity.csv", "w"
        ) as city_file, open(
            "data/processed/tblJoinAddressCity.csv", "w"
        ) as join_file, open(
            "data/processed/tblAddressWithGeoJson.csv", "w"
        ) as address_out_file:
            address_reader = csv.reader(address_file)
            city_writer = csv.writer(city_file, lineterminator="\n")
            join_writer = csv.writer(join_file, lineterminator="\n")
            address_out_writer = csv.writer(address_out_file, lineterminator="\n")

            address_header = next(address_reader)
            address_header_lookup = {h: address_header.index(h) for h in address_header}
            address_out_writer.writerow(address_header)

            city_writer.writerow(["id", "name", "postal_code"])
            join_writer.writerow(["address_id", "city_id"])

            for row in address_reader:
                if (
                    row[address_header_lookup["city_name"]] != ""
                    or row[address_header_lookup["postal_code"]] != ""
                ):
                    key = f'{row[address_header_lookup["city_name"]]}_{row[address_header_lookup["postal_code"]]}'

                    if key not in city_lookup:
                        city_lookup[key] = city_counter
                        city_writer.writerow(
                            [
                                city_counter,
                                row[address_header_lookup["city_name"]],
                                row[address_header_lookup["postal_code"]],
                            ]
                        )
                        city_counter += 1

                    join_writer.writerow(
                        [row[address_header_lookup["address_id"]], city_lookup[key]]
                    )

                if row[address_header_lookup["geodata"]] != "":
                    coordinates = row[address_header_lookup["geodata"]].split(", ")
                    row[address_header_lookup["geodata"]] = json.dumps(
                        {
                            "type": "Point",
                            "coordinates": [coordinates[1], coordinates[0]],
                        }
                    )
                address_out_writer.writerow(row)

    if not action or "persons" in action:
        print("Preprocessing persons")
        # join tlbPerson and tblPersonFirstNames so an update is not needed
        with open("data/clean/tblPerson.csv") as p_file, open(
            "data/clean/tblPersonFirstNames.csv"
        ) as fn_file, open(
            "data/processed/tblPersonWithFirstNames.csv", "w"
        ) as join_file:
            p_reader = csv.reader(p_file)
            fn_reader = csv.reader(fn_file)
            join_writer = csv.writer(join_file, lineterminator="\n")

            p_header = next(p_reader)
            p_header.append("first_names")
            p_header.append("imdb")
            p_header_lookup = {h: p_header.index(h) for h in p_header}

            fn_header = next(fn_reader)
            fn_header_lookup = {h: fn_header.index(h) for h in fn_header}

            join_writer.writerow(p_header)

            fn_lookup = {}
            for row in fn_reader:
                person_id = row[fn_header_lookup["person_id"]]
                if person_id not in fn_lookup:
                    fn_lookup[person_id] = []
                fn_lookup[person_id].append(row[fn_header_lookup["first_name"]])

            for row in p_reader:
                person_id = row[p_header_lookup["person_id"]]
                if person_id in fn_lookup:
                    row.append("|".join(fn_lookup[person_id]))
                else:
                    row.append("")
                if row[p_header_lookup["name"]] == "":
                    row[p_header_lookup["name"]] = (
                        (
                            f'{" / ".join(row[p_header_lookup["first_names"]].split("|"))} '
                            f'{row[p_header_lookup["last_name"]]} '
                            f'{row[p_header_lookup["suffix"]]}'
                        )
                        .replace("  ", " ")
                        .strip()
                    )
                # imdb
                row.append("")
                join_writer.writerow(row)

    if not action or "companies" in action:
        print("Preprocessing companies")
        # split dates in tblCompanyNames
        with open("data/clean/tblCompanyNames.csv") as input_file, open(
            "data/processed/tblCompanyNamesSplitDates.csv", "w"
        ) as output_file:
            i_reader = csv.reader(input_file)
            o_writer = csv.writer(output_file, lineterminator="\n")

            i_header = next(i_reader)
            i_header_lookup = {h: i_header.index(h) for h in i_header}

            o_header = ["company_id", "name", "date_start", "date_end", "sequential_id"]
            o_writer.writerow(o_header)

            for row in i_reader:
                date = row[i_header_lookup["date"]]
                if "/" in date:
                    (date_start, date_end) = date.split("/")
                else:
                    date_start = date
                    date_end = date
                row[i_header_lookup["date"] : i_header_lookup["date"] + 1] = (
                    date_start,
                    date_end,
                )
                o_writer.writerow(row)

    if not action or "programmes" in action:
        print("Preprocessing programmes")
        # add Vooruit image urls to programme
        # calculate programme dates
        with open("data/clean/tblProgramme.csv") as programme_file, open(
            "data/clean/images/programmes_image_urls.csv"
        ) as programme_image_file, open(
            "data/clean/tblProgrammeBoxOffice.csv"
        ) as programme_box_office_file, open(
            "data/clean/tblProgrammeDate.csv"
        ) as programme_date_file, open(
            "data/processed/tblProgrammeWithImagesAndBoxOffice.csv", "w"
        ) as programme_ouptut_file, open(
            "data/processed/tblProgrammeDateCalculated.csv", "w"
        ) as programme_date_output_file:
            p_reader = csv.reader(programme_file)
            i_reader = csv.reader(programme_image_file)
            pbo_reader = csv.reader(programme_box_office_file)
            pd_reader = csv.reader(programme_date_file)
            po_writer = csv.writer(programme_ouptut_file, lineterminator="\n")
            pdo_writer = csv.writer(programme_date_output_file, lineterminator="\n")

            p_header = next(p_reader)
            p_header_lookup = {h: p_header.index(h) for h in p_header}

            i_header = next(i_reader)
            i_header_lookup = {h: i_header.index(h) for h in i_header}

            pbo_header = next(pbo_reader)
            pbo_header_lookup = {h: pbo_header.index(h) for h in pbo_header}

            pd_header = next(pd_reader)
            pd_header_lookup = {h: pd_header.index(h) for h in pd_header}

            pdo_header = [
                "programme_date_id",
                "programme_id",
                "date_start",
                "date_end",
                "dates_mentioned",
            ]
            pdo_writer.writerow(pdo_header)

            p_header.append("vooruit_image_url")
            p_header.extend(
                [
                    "gross_income",
                    "number_of_tickets",
                    "mean_price",
                    "taxes_and_copyrights",
                    "net_income",
                    "cheapest_ticket",
                    "most_expensive_ticket",
                ]
            )
            po_writer.writerow(p_header)

            i_lookup = {}
            for row in i_reader:
                i_lookup[row[i_header_lookup["programme_id"]]] = row[
                    i_header_lookup["image_url"]
                ]

            pbo_lookup = {}
            for row in pbo_reader:
                pbo_lookup[row[pbo_header_lookup["programme_id"]]] = row[1:]

            p_lookup = {}
            re_mentioned_dates = re.compile(r"[(]([a-z0-9- X]+)[)]")
            for row in p_reader:
                programme_id = row[p_header_lookup["programme_id"]]
                p_lookup[programme_id] = {
                    "is_week": "Vertoningsweek"
                    in row[p_header_lookup["programme_info"]],
                    "dates_mentioned": re_mentioned_dates.findall(
                        row[p_header_lookup["programme_info"]]
                    ),
                }
                if programme_id in i_lookup:
                    row.append(i_lookup[programme_id])
                else:
                    row.append("")
                if programme_id in pbo_lookup:
                    row.extend(pbo_lookup[programme_id])
                else:
                    row.extend([""] * 7)
                po_writer.writerow(row)

            counter = 0
            for row in pd_reader:
                counter += 1
                programme_id = row[pd_header_lookup["programme_id"]]
                date = row[pd_header_lookup["programme_date"]]
                if "{" in date:
                    multiple = edtf.parse_edtf(date)
                    date_start = str(multiple.objects[0])
                    date_end = str(multiple.objects[-1])
                elif "/" in date:
                    interval = edtf.parse_edtf(date)
                    date_start = str(interval.lower)
                    date_end = str(interval.upper)
                elif p_lookup[programme_id]["is_week"]:
                    date_start = date
                    if "193X" in date:
                        date_end = datetime.datetime.strftime(
                            datetime.datetime.strptime(
                                date.replace("193X", "1935"), "%Y-%m-%d"
                            )
                            + datetime.timedelta(days=7),
                            "%Y-%m-%d",
                        ).replace("1935", "193X")
                    else:
                        date_end = datetime.datetime.strftime(
                            datetime.datetime.strptime(date, "%Y-%m-%d")
                            + datetime.timedelta(days=7),
                            "%Y-%m-%d",
                        )
                else:
                    date_start = date
                    date_end = date
                dates_mentioned = "|".join(p_lookup[programme_id]["dates_mentioned"])
                pdo_writer.writerow(
                    [counter, programme_id, date_start, date_end, dates_mentioned]
                )

    if not action or "programme_items" in action:
        print("Preprocessing programme items")
        # add ids to the programme_item mentioned title relations
        with open("data/clean/tblProgrammeItem.csv") as input_file, open(
            "data/processed/tblJoinProgrammeItemMentionedTitle.csv", "w"
        ) as output_file:
            i_reader = csv.reader(input_file)
            o_writer = csv.writer(output_file, lineterminator="\n")

            i_header = next(i_reader)
            i_header_lookup = {h: i_header.index(h) for h in i_header}

            o_writer.writerow(
                [
                    "programme_item_id",
                    "mentioned_title_id",
                    "programme_item_mentioned_title_id",
                ]
            )

            counter = 0
            for row in i_reader:
                for mentioned_title_id in row[
                    i_header_lookup["film_variation_id"]
                ].split("|"):
                    if mentioned_title_id != "":
                        counter += 1
                        o_writer.writerow(
                            [
                                row[i_header_lookup["programme_item_id"]],
                                mentioned_title_id,
                                counter,
                            ]
                        )

    if not action or "venues" in action:
        print("Preprocessing venues")
        # add screen and seat information (as json) to venue
        with open("data/clean/tblVenue.csv") as venue_file, open(
            "data/clean/tblVenueScreen.csv"
        ) as screen_file, open("data/clean/tblVenueSeats.csv") as seat_file, open(
            "data/processed/tblVenueWithScreensAndSeats.csv", "w"
        ) as out_file:

            venue_reader = csv.reader(venue_file)
            screen_reader = csv.reader(screen_file)
            seat_reader = csv.reader(seat_file)
            out_writer = csv.writer(out_file, lineterminator="\n")

            venue_header = next(venue_reader)
            venue_header_lookup = {h: venue_header.index(h) for h in venue_header}

            screen_header = next(screen_reader)
            screen_header_lookup = {h: screen_header.index(h) for h in screen_header}

            seat_header = next(seat_reader)
            seat_header_lookup = {h: seat_header.index(h) for h in seat_header}

            venue_header.append("screens")
            venue_header.append("seats")
            out_writer.writerow(venue_header)

            def get_year_of_item(years):
                if RE_SIMPLE_YEAR.match(years):
                    return int(years)
                if RE_SIMPLE_INTERVAL.match(years):
                    return int(years[:4])
                if RE_MEMBERS.match(years):
                    return int(years[1:5])
                # https://github.com/ixc/python-edtf/issues/24
                years = years.replace("X", "u")
                if "/" in years:
                    years = years.replace("..", "open")
                if years[-1] == "/":
                    years += "unknown"
                # Bug: 1924?/19XX
                if years == "1924?/19uu":
                    years = "1924/19uu"
                # Bug: 197X/..
                if years == "197u/open":
                    years = "197u"
                edtf_object = edtf.parse_edtf(years)
                if hasattr(edtf_object, "lower"):
                    edtf_object = edtf_object.lower
                if isinstance(edtf_object, list):
                    edtf_object = edtf_object[0]
                return int(time.strftime("%Y", edtf_object.lower_strict()))

            screen_lookup = {}
            screen_lookup_lookup = {}
            for row in screen_reader:
                venue_id = row[screen_header_lookup["venue_id"]]
                if venue_id not in screen_lookup:
                    screen_lookup[venue_id] = []
                    screen_lookup_lookup[venue_id] = set()
                key = f'{row[screen_header_lookup["number_of_screens"]]}___{row[screen_header_lookup["years"]]}'
                if key not in screen_lookup_lookup[venue_id]:
                    screen_lookup[venue_id].append(
                        [
                            row[screen_header_lookup["number_of_screens"]],
                            row[screen_header_lookup["years"]],
                            get_year_of_item(row[screen_header_lookup["years"]]),
                        ]
                    )
                    screen_lookup_lookup[venue_id].add(key)

            seat_lookup = {}
            seat_lookup_lookup = {}
            for row in seat_reader:
                venue_id = row[seat_header_lookup["venue_id"]]
                if venue_id not in seat_lookup:
                    seat_lookup[venue_id] = []
                    seat_lookup_lookup[venue_id] = set()
                key = f'{row[seat_header_lookup["number_of_seats"]]}___{row[seat_header_lookup["years"]]}'
                if key not in seat_lookup_lookup[venue_id]:
                    seat_lookup[venue_id].append(
                        [
                            row[seat_header_lookup["number_of_seats"]],
                            row[seat_header_lookup["years"]],
                            get_year_of_item(row[screen_header_lookup["years"]]),
                        ]
                    )
                    seat_lookup_lookup[venue_id].add(key)

            for row in venue_reader:
                venue_id = row[venue_header_lookup["venue_id"]]

                if venue_id in screen_lookup:
                    row.append(
                        json.dumps(
                            [["Number of screens", "Years"]]
                            + [
                                [item[0], item[1]]
                                for item in sorted(
                                    screen_lookup[venue_id], key=lambda l: l[2]
                                )
                            ]
                        )
                    )
                else:
                    row.append("")

                if venue_id in seat_lookup:
                    row.append(
                        json.dumps(
                            [["Number of seats", "Years"]]
                            + [
                                [item[0], item[1]]
                                for item in sorted(
                                    seat_lookup[venue_id], key=lambda l: l[2]
                                )
                            ]
                        )
                    )
                else:
                    row.append("")

                out_writer.writerow(row)

    if not action or "censorship" in action:
        print("Preprocessing censorship")
        # Convert ratings
        with open("data/clean/tblCensorship.csv") as input_file, open(
            "data/processed/tblCensorship.csv", "w"
        ) as output_file:

            i_reader = csv.reader(input_file)
            o_writer = csv.writer(output_file, lineterminator="\n")

            i_header = next(i_reader)
            i_header.append("censorship_episode_id")
            i_header.append("censorship_appeal_id")
            ihl = {h: i_header.index(h) for h in i_header}

            o_writer.writerow(i_header)

            conv = {
                "": "",
                "A": "all",
                "C": "all (after cut)",
                "R": "16+",
                "KT": "all",
                "KT 4/1": "all",
                "KT 3/1": "all",
                "KT Z.V.": "all",
                "KT 12 JAAR": "12+",
                "KT 3/1 12 JAAR EN 1 KNT": "12+",
                "KNT": "16+",
                "KNT 3/1": "16+",
            }

            censorship_episode_counter = 0
            censorship_appeal_counter = 0

            for row in i_reader:
                row[ihl["rating"]] = conv[row[ihl["rating"]].strip()]

                if row[ihl["episode_id"]] != "":
                    censorship_episode_counter += 1
                    row.append(censorship_episode_counter)
                else:
                    row.append("")

                if row[ihl["has_appeal"]] != "":
                    censorship_appeal_counter += 1
                    row.append(censorship_appeal_counter)
                else:
                    row.append("")

                o_writer.writerow(row)

    if not action or "censorship_category" in action:
        print("Preprocessing censorship_category")
        shutil.copyfile(
            "data/fixtures/tblCensorshipCutMainCategory.csv",
            "data/processed/tblCensorshipCutMainCategory.csv",
        )
        shutil.copyfile(
            "data/fixtures/tblCensorshipCutDetailedCategory.csv",
            "data/processed/tblCensorshipCutDetailedCategory.csv",
        )


if __name__ == "__main__":
    typer.run(main)
