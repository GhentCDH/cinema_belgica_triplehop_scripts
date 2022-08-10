import csv
import datetime
import json
import typing

import isbnlib
import typer

M = {
    'januar': '01',
    'jan': '01',
    'februar': '02',
    'feb': '02',
    'märz': '03',
    'april': '04',
    'apr': '04',
    'mai': '05',
    'juni': '06',
    'jun': '06',
    'juli': '07',
    'jul': '07',
    'august': '08',
    'aug': '08',
    'september': '09',
    'sep': '09',
    'oktober': '10',
    'okt': '10',
    'november': '11',
    'nov': '11',
    'dezember': '12',
    'dez': '12',
}

FILMPORTAL = {
    'https://www.filmportal.de/film/schoenheit-siegt_454c5f8d97904e839e3b785e26b96471': "website film 'Schönheit siegt'",
    'https://www.filmportal.de/film/das-geheimnis-der-diabolit_9fbf4ac5bd0e4493bd7df10980dc224e': "website film 'Das Geheimnis der Diabolit'",
    'https://www.filmportal.de/film/die-graefin-mit-dem-reiher_0105c5a6c30342918455c8ac647ced9e': "website film 'Die Gräfin mit dem Reiher'",
    'https://www.filmportal.de/film/panzerschrank-nr-13_28b31db6d5934ddaa5fa863375181162': "website film 'Panzerschrank Nr.13'",
    'https://www.filmportal.de/film/der-schwarze-meister_9b2fffdb876445968baf3034526b972e': "website film 'Der schwarze Meister'",
    'https://www.filmportal.de/en/movie/das-tal-der-vergeltung_ea43d4a6b3605006e03053d50b37753d': "website film 'Das Tal der Vergeltung'",
    'https://www.filmportal.de/film/die-brigantin-von-costiliza-1-teil_a16d671b08dd4a098734d5f0d0aa1066': "website film 'Die Brigantin von Costiliza. 1. Teil'",
    'https://www.filmportal.de/film/das-schachdorf_fabf6b830d6441478fdba8ef74aeab60': "website film 'Das Schachdorf'",
}

EARLYCINEMA = {
    'http://earlycinema.dch.phil-fak.uni-koeln.de/films/view/29068': "website film 'Das Mädchen von Hidalgo'",
    'http://earlycinema.dch.phil-fak.uni-koeln.de/films/view/21725': "website film 'Die Fahrt ins Glücksland'",
    'http://earlycinema.dch.phil-fak.uni-koeln.de/films/view/35486': "website film 'Der Todescowboy'",
    'http://earlycinema.dch.phil-fak.uni-koeln.de/films/view/25265': "website film 'Der Hoteldieb mit der vierten Hand'",
}

def add_source(
    type: str,
    id: str,
    properties: list,
    source_type: str,
    source_id: str,
    sources: typing.Dict,
    source_props: typing.Dict = None,
):
    if source_props is None:
        source_props = {}
    # prevent sources from being added more than once
    key = '_'.join([type, id, '_|_'.join(properties), source_type, source_id])
    if key not in sources:
        sources[key] = [
            type,
            id,
            '|'.join(properties),
            source_type,
            source_id,
            source_props
        ]
    else:
        for k, v in source_props.items():
            if k in sources[key][5]:
                sources[key][5][k].update(v)
            else:
                sources[key][5][k] = v


def write_sources(
    filename: str,
    header: typing.List[str],
    sources: typing.Dict
):
    with open(filename, 'w') as out_file:
        csv_writer = csv.writer(out_file, lineterminator='\n')
        csv_writer.writerow(header)

        for source in sources.values():
            source_props = source[5]
            source_props_w = {}
            for k, v in source_props.items():
                source_props_w[k] = sorted(list(v))
            source[5] = json.dumps(source_props_w)
            csv_writer.writerow(source)



def main():
    print('Reading base data and creating data structures')
    entity_sources = {}
    relation_sources = {}


    publications = []
    with open('data/clean/tblPublication.csv') as input_file:
        i_reader = csv.reader(input_file)

        # skip header row
        next(i_reader)

        for row in i_reader:
            publications.append(row)

    publication_lookup = {}
    publication_ds_lookup = {}

    publication_type_lookup = {}
    with open('data/clean/tblPublicationType.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            publication_type_lookup[row[i_header_lookup['type']]] = row[i_header_lookup['id']]


    archive_items = []
    with open('data/clean/tblArchiveItem.csv') as input_file:
        i_reader = csv.reader(input_file)

        # skip header row
        next(i_reader)

        for row in i_reader:
            archive_items.append(row)

    archive_item_lookup = {}
    archive_item_ds_lookup = {}


    archive_lookup = {}
    archives = []
    with open('data/clean/tblArchive.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            archives.append(row)
            archive_lookup[row[i_header_lookup['name']]] = row[i_header_lookup['id']]


    invalid_sources = set()


    venue_header_lookup = {}
    venues = {}
    with open('data/processed/tblVenueWithScreensAndSeats.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        venue_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            venues[row[venue_header_lookup['venue_id']]] = row

    address_header_lookup = {}
    addresses = {}
    with open('data/processed/tblAddressWithGeoJson.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        address_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            addresses[row[address_header_lookup['address_id']]] = row

    programme_item_mentioned_titles = {}
    with open('data/processed/tblJoinProgrammeItemMentionedTitle.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            programme_item_id = row[i_header_lookup['programme_item_id']]
            if programme_item_id not in programme_item_mentioned_titles:
                programme_item_mentioned_titles[programme_item_id] = []
            programme_item_mentioned_titles[programme_item_id].append(row[i_header_lookup['programme_item_mentioned_title_id']])


    # look up programme dates for dataset 12
    programme_link_12 = {}
    programme_dates = {}
    with open('data/clean/source_links/tblProgrammeSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            ds = row[i_header_lookup['dataset']]
            if '12_' in ds:
                programme_link_12[row[i_header_lookup['programme_id']]] = [ds, row[i_header_lookup['row']]]

    with open('data/clean/tblProgrammeDate.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['programme_id']] in programme_link_12:
                ds, row_id = programme_link_12[row[i_header_lookup['programme_id']]]
                if ds not in programme_dates:
                    programme_dates[ds] = {}
                programme_dates[ds][row_id] = row[i_header_lookup['programme_date']]

    film_teneo = {}
    with open('data/clean/tblFilm.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            film_teneo[row[i_header_lookup['film_id']]] = row[i_header_lookup['kadoc_id']].split('|')

    ####################
    # 01.csv -> 04.csv #
    ####################
    print('Processing 01.csv -> 04.csv')

    with open('data/original/source_links/tblFilmTitleVariationSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ['01.csv', '02.csv']:
                add_source(
                    'mentioned_film_title',
                    row[i_header_lookup['film_variation_id']],
                    ['title'],
                    'archive_item',
                    '1',
                    entity_sources,
                )
            if row[i_header_lookup['dataset']] in ['03.csv', '04.csv']:
                add_source(
                    'mentioned_film_title',
                    row[i_header_lookup['film_variation_id']],
                    ['title'],
                    'archive_item',
                    '2',
                    entity_sources,
                )

    with open('data/original/source_links/tblJoinFilmCompanySource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ['01.csv', '02.csv']:
                add_source(
                    'film_company',
                    row[i_header_lookup['film_company_id']],
                    ['__rel__', 'type'],
                    'archive_item',
                    '1',
                    relation_sources,
                )
            if row[i_header_lookup['dataset']] in ['03.csv', '04.csv']:
                add_source(
                    'film_company',
                    row[i_header_lookup['film_company_id']],
                    ['__rel__', 'type'],
                    'archive_item',
                    '2',
                    relation_sources,
                )

    with open('data/original/source_links/tblFilmSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ['01.csv', '02.csv']:
                add_source(
                    'film',
                    row[i_header_lookup['film_id']],
                    ['length', 'length_unit'],
                    'archive_item',
                    '1',
                    entity_sources,
                )
            if row[i_header_lookup['dataset']] in ['03.csv', '04.csv']:
                add_source(
                    'film',
                    row[i_header_lookup['film_id']],
                    ['length', 'length_unit'],
                    'archive_item',
                    '2',
                    entity_sources,
                )

    censorship_lookup = {}
    with open('data/original/source_links/tblCensorshipSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ['01.csv', '02.csv']:
                censorship_lookup[row[i_header_lookup['censorship_id']]] = '1'
            elif row[i_header_lookup['dataset']] in ['03.csv', '04.csv']:
                censorship_lookup[row[i_header_lookup['censorship_id']]] = '2'
            else:
                raise Exception('Censorhip dataset other than 01 02 03 04 found')


    with open('data/processed/tblCensorship.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}
        for row in i_reader:
            censorship_id = row[i_header_lookup['censorship_id']]
            archive_item_id = censorship_lookup[censorship_id]

            add_source(
                'censorship',
                censorship_id,
                ['date', 'rating', 'motivation'],
                'archive_item',
                archive_item_id,
                    entity_sources,
            )

            if row[i_header_lookup['has_appeal']] != '':
                add_source(
                    'censorship_appeal',
                    row[i_header_lookup['censorship_appeal_id']],
                    ['__rel__'],
                    'archive_item',
                    archive_item_id,
                    relation_sources,
                )

            if row[i_header_lookup['film_id']] != '':
                add_source(
                    'film_censorship',
                    censorship_id,
                    ['__rel__'],
                    'archive_item',
                    archive_item_id,
                    relation_sources,
                )

    with open('data/clean/tblCensorshipCut.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            cut_id = row[i_header_lookup['cut_id']]
            censorship_id = row[i_header_lookup['censorship_id']]
            archive_item_id = censorship_lookup[censorship_id]

            add_source(
                'censorship_cut',
                cut_id,
                ['date', 'comment_nl', 'comment_fr'],
                'archive_item',
                archive_item_id,
                entity_sources,
            )

            add_source(
                'censorship_cut',
                cut_id,
                ['__rel__'],
                'archive_item',
                archive_item_id,
                relation_sources,
            )

    ############################
    # 05_*.csv ->  08_*.csv    #
    ############################

    print('Creating sources for datasets 05.csv -> 08_2.csv')
    for ds in ['05_1', '05_2', '06', '07', '08_2']:
        print(f'Processing {ds}_sources')
        with open(f'data/clean/datasets/sources_input/{ds}_sources.csv') as input_file:
            i_reader = csv.reader(input_file)

            i_header = next(i_reader)
            i_header_lookup = {h: i_header.index(h) for h in i_header}

            for row in i_reader:
                publication_id_tmp = row[i_header_lookup['publication_id']]
                if 'archive_id' in i_header_lookup:
                    archive_id_tmp = row[i_header_lookup['archive_id']]
                else:
                    archive_id_tmp = ''

                ds_key = (
                    row[i_header_lookup['Bron titel']].lower() +
                    '_' +
                    row[i_header_lookup['Bron datum']].lower() +
                    '_' +
                    row[i_header_lookup['Vindplaats']].lower()
                )

                if publication_id_tmp != '':
                    if publication_id_tmp not in publication_lookup:
                        publication_id = str(len(publications) + 1)

                        isbn = ''
                        if 'isbn_issn' in i_header_lookup:
                            isbn_issn = row[i_header_lookup['isbn_issn']]
                            isbn_can = isbnlib.canonical(isbn_issn)
                            if isbnlib.is_isbn10(isbn_can):
                                isbn = isbnlib.to_isbn13(isbn_can)
                            elif isbnlib.is_isbn13(isbn_can):
                                isbn = isbn_can


                        publications.append({
                            'publication_id': publication_id,
                            'editorial_comment': row[i_header_lookup['publication_comment']],
                            'digitally_available': '',
                            'publication_type': row[i_header_lookup['publication_type']],
                            'isbn': isbn,
                            'issn': '',
                            'title': row[i_header_lookup['title']],
                            'book_journal_title': '',
                            'publication_date': row[i_header_lookup['publication_date']].replace('-', '/'),
                            'publication_volume': row[i_header_lookup['publication_volume']],
                            'publication_number': row[i_header_lookup['publication_number']],
                            'author': row[i_header_lookup['author']],
                            'editor': row[i_header_lookup['editor']],
                            'place': row[i_header_lookup['place']],
                            'publisher': row[i_header_lookup['publisher']],
                            'start_page': row[i_header_lookup['start_page']] if 'start_page' in i_header_lookup else '',
                            'end_page': row[i_header_lookup['end_page']] if 'end_page' in i_header_lookup else '',
                            'url': row[i_header_lookup['publication_url']],
                        }.values())
                        publication_lookup[publication_id_tmp] = publication_id
                    publication_ds_lookup[ds_key] = publication_id_tmp
                elif archive_id_tmp != '':
                    if archive_id_tmp not in archive_item_lookup:
                        if row[i_header_lookup['institution']] == '':
                            archive_id = ''

                        if row[i_header_lookup['institution']].lower() not in archive_lookup:
                            archive_id = str(len(archives) + 1)
                            archives.append({
                                'id': archive_id,
                                'name': row[i_header_lookup['institution']],
                                'address_id': '',
                            }.values())
                            archive_lookup[row[i_header_lookup['institution']].lower()] = archive_id
                        else:
                            archive_id = archive_lookup[row[i_header_lookup['institution']].lower()]

                        archive_item_id = str(len(archive_items) + 1)
                        archive_items.append({
                            'id': archive_item_id,
                            'inventory_id': row[i_header_lookup['inventory']],
                            'inventory_description': '',
                            'item_number': row[i_header_lookup['item_nr']],
                            'name': row[i_header_lookup['description']],
                            'url': row[i_header_lookup['archive_url']],
                            'archive_id': archive_id,
                            'editorial_comment': row[i_header_lookup['archive_comment']],
                        }.values())
                        archive_item_lookup[archive_id_tmp] = archive_item_id
                    archive_item_ds_lookup[ds_key] = archive_id_tmp
                else:
                    invalid_sources.add(ds_key)


    print('Processing 05_1.csv')
    with open('data/clean/datasets/05_1.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            key = (
                row[i_header_lookup['Bron titel']].lower() +
                '_' +
                row[i_header_lookup['Bron datum']].lower() +
                '_' +
                row[i_header_lookup['Vindplaats']].lower()
            )

            source_type = ''
            source_id = ''
            if key in publication_ds_lookup:
                source_type = 'publication'
                source_id = publication_lookup[publication_ds_lookup[key]]
            elif key in archive_item_ds_lookup:
                source_type = 'archive_item'
                source_id = archive_item_lookup[archive_item_ds_lookup[key]]
            elif key in invalid_sources:
                print(f'Source with key "{key}" is not a publication and not an archive item.')
                continue
            else:
                print(f'Source with key "{key}"  not found')
                print(row)
                continue

            source_props = {}
            if row[i_header_lookup['Bron paginanummer']] != '':
                source_props['page_number'] = set([row[i_header_lookup['Bron paginanummer']]])

            if row[i_header_lookup['venue_id']] != '':
                try:
                    venue = venues[row[i_header_lookup['venue_id']]]
                except KeyError:
                    print('Venue id not found')
                    print(row[i_header_lookup['venue_id']])
                    continue
                venue_id = venue[venue_header_lookup['sequential_id']]

                if row[i_header_lookup['Naam bioscoop standaard']].lower() == venue[venue_header_lookup['name']].lower():
                    add_source(
                        'venue',
                        venue_id,
                        ['name'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                if row[i_header_lookup['Aantal zalen']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['screens'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                if row[i_header_lookup['Aantal zitplaatsen totaal']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['seats'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                address_id = venue[venue_header_lookup['address_id']]
                if (
                    address_id != ''
                    and addresses[address_id][address_header_lookup['street_name']].lower() == f'{row[i_header_lookup["Adres standaard"]].lower()} {row[i_header_lookup["Huisnummer standaard"]]}'
                ) :
                    add_source(
                        'address',
                        venue_id,
                        ['__rel__'],
                        source_type,
                        source_id,
                        relation_sources,
                        source_props,
                    )

    print('Processing 05_2.csv')
    with open('data/clean/datasets/05_2.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            key = (
                row[i_header_lookup['Bron titel']].lower() +
                '_' +
                row[i_header_lookup['Bron datum']].lower() +
                '_' +
                row[i_header_lookup['Vindplaats']].lower()
            ).replace(r'\n', '\n')

            source_type = ''
            source_id = ''
            if key in publication_ds_lookup:
                source_type = 'publication'
                source_id = publication_lookup[publication_ds_lookup[key]]
            elif key in archive_item_ds_lookup:
                source_type = 'archive_item'
                source_id = archive_item_lookup[archive_item_ds_lookup[key]]
            elif key in invalid_sources:
                print(f'Source with key "{key}" is not a publication and not an archive item.')
                continue
            else:
                print(f'Source with key "{key}"  not found')
                print(row)
                continue

            source_props = {}
            if row[i_header_lookup['Bron paginanummer']] != '':
                source_props['page_number'] = set([row[i_header_lookup['Bron paginanummer']]])

            if row[i_header_lookup['venue_id']] != '':
                try:
                    venue = venues[row[i_header_lookup['venue_id']]]
                except KeyError:
                    print('Venue id not found')
                    print(row[i_header_lookup['venue_id']])
                    continue
                venue_id = venue[venue_header_lookup['sequential_id']]

                if row[i_header_lookup['Naam bioscoop STANDAARD']].lower() == venue[venue_header_lookup['name']].lower():
                    add_source(
                        'venue',
                        venue_id,
                        ['name'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                if row[i_header_lookup['Aantal zalen']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['screens'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                if row[i_header_lookup['Aantal zitplaatsen totaal']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['seats'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                address_id = venue[venue_header_lookup['address_id']]
                if (
                    address_id != ''
                    and addresses[address_id][address_header_lookup['street_name']].lower() == f'{row[i_header_lookup["Adres STANDAARD"]].lower()} {row[i_header_lookup["Huisnr."]]}'
                ) :
                    add_source(
                        'address',
                        venue_id,
                        ['__rel__'],
                        source_type,
                        source_id,
                        relation_sources,
                        source_props,
                    )


    print('Processing 06.csv')
    with open('data/clean/datasets/06.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            source_titles = row[i_header_lookup['Bron titel']].lower().split(' + ')
            for source_title in source_titles:
                key = (
                    source_title +
                    '_' +
                    row[i_header_lookup['Bron datum']].lower() +
                    '_' +
                    row[i_header_lookup['Vindplaats']].lower()
                )

                source_type = ''
                source_id = ''
                if key in publication_ds_lookup:
                    source_type = 'publication'
                    source_id = publication_lookup[publication_ds_lookup[key]]
                elif key in archive_item_ds_lookup:
                    source_type = 'archive_item'
                    source_id = archive_item_lookup[archive_item_ds_lookup[key]]
                elif key in invalid_sources:
                    print(f'Source with key "{key}" is not a publication and not an archive item.')
                    continue
                else:
                    print(f'Source with key "{key}"  not found')
                    print(row)
                    continue

                if row[i_header_lookup['venue_id']] != '':
                    try:
                        venue = venues[row[i_header_lookup['venue_id']]]
                    except KeyError:
                        print('Venue id not found')
                        print(row[i_header_lookup['venue_id']])
                        continue
                    venue_id = venue[venue_header_lookup['sequential_id']]

                    if row[i_header_lookup['Naam bioscoop standaard']].lower() == venue[venue_header_lookup['name']].lower():
                        add_source(
                            'venue',
                            venue_id,
                            ['name'],
                            source_type,
                            source_id,
                            entity_sources,
                        )

                    if row[i_header_lookup['Aantal zalen']] != '':
                        add_source(
                            'venue',
                            venue_id,
                            ['screens'],
                            source_type,
                            source_id,
                            entity_sources,
                        )

                    if row[i_header_lookup['Aantal zitplaatsen totaal']] != '':
                        add_source(
                            'venue',
                            venue_id,
                            ['seats'],
                            source_type,
                            source_id,
                            entity_sources,
                        )

                    address_id = venue[venue_header_lookup['address_id']]
                    if (
                        address_id != ''
                        and addresses[address_id][address_header_lookup['street_name']].lower() == f'{row[i_header_lookup["Adres standaard"]].lower()} {row[i_header_lookup["Huisnummer standaard"]]}'
                    ) :
                        add_source(
                            'address',
                            venue_id,
                            ['__rel__'],
                            source_type,
                            source_id,
                            relation_sources,
                        )

    print('Processing 07.csv')
    with open('data/clean/datasets/07.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            key = (
                row[i_header_lookup['Bron titel']].lower() +
                '_' +
                row[i_header_lookup['Bron datum']].lower() +
                '_' +
                row[i_header_lookup['Vindplaats']].lower()
            ).replace(r'\n', '\n')

            source_type = ''
            source_id = ''
            if key in publication_ds_lookup:
                source_type = 'publication'
                source_id = publication_lookup[publication_ds_lookup[key]]
            elif key in archive_item_ds_lookup:
                source_type = 'archive_item'
                source_id = archive_item_lookup[archive_item_ds_lookup[key]]
            elif key in invalid_sources:
                print(f'Source with key "{key}" is not a publication and not an archive item.')
                continue
            else:
                print(f'Source with key "{key}"  not found')
                print(row)
                continue

            source_props = {}
            if row[i_header_lookup['Bron p.']] != '':
                source_props['page_number'] = set([row[i_header_lookup['Bron p.']]])

            if row[i_header_lookup['venue_id']] != '':
                try:
                    venue = venues[row[i_header_lookup['venue_id']]]
                except KeyError:
                    print('Venue id not found')
                    print(row[i_header_lookup['venue_id']])
                    continue
                venue_id = venue[venue_header_lookup['sequential_id']]

                if row[i_header_lookup['Naam bioscoop STANDAARD']].lower() == venue[venue_header_lookup['name']].lower():
                    add_source(
                        'venue',
                        venue_id,
                        ['name'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                if row[i_header_lookup['Aantal zalen']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['screens'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                if row[i_header_lookup['Aantal zitplaatsen totaal']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['seats'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                address_id = venue[venue_header_lookup['address_id']]
                if (
                    address_id != ''
                    and addresses[address_id][address_header_lookup['street_name']].lower() == f'{row[i_header_lookup["Adres STANDAARD"]].lower()} {row[i_header_lookup["Huisnr."]]}'
                ) :
                    add_source(
                        'address',
                        venue_id,
                        ['__rel__'],
                        source_type,
                        source_id,
                        relation_sources,
                        source_props,
                    )

    print('Processing 08_1.csv')
    with open('data/clean/datasets/08_1.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['venue_id']] != '':
                try:
                    venue = venues[row[i_header_lookup['venue_id']]]
                except KeyError:
                    print('Venue id not found')
                    print(row[i_header_lookup['venue_id']])
                    continue

                venue_id = venue[venue_header_lookup['sequential_id']]

                if row[i_header_lookup['Naam bioscoop STANDAARD']].lower() == venue[venue_header_lookup['name']].lower():
                    add_source(
                        'venue',
                        venue_id,
                        ['name'],
                        'publication',
                        '1',
                        entity_sources,
                    )

                if row[i_header_lookup['Aantal zalen']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['screens'],
                        'publication',
                        '1',
                        entity_sources,
                    )

                if row[i_header_lookup['Aantal zitplaatsen totaal']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['seats'],
                        'publication',
                        '1',
                        entity_sources,
                    )

                address_id = venue[venue_header_lookup['address_id']]
                if (
                    address_id != ''
                    and addresses[address_id][address_header_lookup['street_name']].lower() == f'{row[i_header_lookup["Adres STANDAARD"]].lower()} {row[i_header_lookup["Huisnr."]]}'
                ) :
                    add_source(
                        'address',
                        venue_id,
                        ['__rel__'],
                        'publication',
                        '1',
                        relation_sources,
                    )

    print('Processing 08_2.csv')
    with open('data/clean/datasets/08_2.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            key = (
                row[i_header_lookup['Bron titel']].lower() +
                '_' +
                row[i_header_lookup['Bron datum']].lower() +
                '_' +
                row[i_header_lookup['Vindplaats']].lower()
            ).replace(r'\n', '\n')

            source_type = ''
            source_id = ''
            if key in publication_ds_lookup:
                source_type = 'publication'
                source_id = publication_lookup[publication_ds_lookup[key]]
            elif key in archive_item_ds_lookup:
                source_type = 'archive_item'
                source_id = archive_item_lookup[archive_item_ds_lookup[key]]
            elif key in invalid_sources:
                print(f'Source with key "{key}" is not a publication and not an archive item.')
                continue
            else:
                print(f'Source with key "{key}"  not found')
                print(row)
                continue

            source_props = {}
            if row[i_header_lookup['Bron paginanummer']] != '':
                source_props['page_number'] = set([row[i_header_lookup['Bron paginanummer']]])

            if row[i_header_lookup['venue_id']] != '':
                try:
                    venue = venues[row[i_header_lookup['venue_id']]]
                except KeyError:
                    print('Venue id not found')
                    print(row[i_header_lookup['venue_id']])
                    continue
                venue_id = venue[venue_header_lookup['sequential_id']]

                if row[i_header_lookup['Naam bioscoop STANDAARD']].lower() == venue[venue_header_lookup['name']].lower():
                    add_source(
                        'venue',
                        venue_id,
                        ['name'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                if row[i_header_lookup['Aantal zalen']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['screens'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                if row[i_header_lookup['Aantal zitplaatsen totaal']] != '':
                    add_source(
                        'venue',
                        venue_id,
                        ['seats'],
                        source_type,
                        source_id,
                        entity_sources,
                        source_props,
                    )

                address_id = venue[venue_header_lookup['address_id']]
                if (
                    address_id != ''
                    and addresses[address_id][address_header_lookup['street_name']].lower() == f'{row[i_header_lookup["Adres STANDAARD"]].lower()} {row[i_header_lookup["Huisnr."]]}'
                ) :
                    add_source(
                        'address',
                        venue_id,
                        ['__rel__'],
                        source_type,
                        source_id,
                        relation_sources,
                        source_props,
                    )

    ####################
    # 09_*.csv ->  #
    ####################
    print('Creating sources for datasets 09_*.csv ->')

    programming_sources = {}
    ds_configs = {
        '09_1.csv': ['Bron vindplaats', '', '', 'Bron datum', '', '', 'ID'],
        '09_2.csv': ['Brontitel', '', '', 'Brondatum', '', '', 'ID'],
        '09_3.csv': ['Bron_vindplaats', '', '', 'Bron_datum', '', '', 'ID'],
        '09_4.csv': ['', '', '', '', 'Vertoningsweek', '', '', 'ID'],
        '09_5.csv': ['Bron vindplaats', '', '', 'Bron datum', '', '', 'ID'],
        '10_1.csv': ['Bron titel', '', '', 'Bron datum', 'Vertoningsweek', 'Bron paginanummer', 'ID'],
        '10_2.csv': ['Bron titel', '', '', 'Bron datum', 'Vertoningsweek', 'Bron p.nr.', 'ID'],
        '10_4.csv': ['Bron titel', '', '', 'Bron datum', 'Vertoningsweek', 'Bron p.nr.', 'ID'],
        '10_5.csv': ['Bron titel', '', '', 'Bron datum', 'Vertoningsweek', 'Bron p.nr.', 'ID'],
        '11.csv': ['Bron titel', '', '', '', 'Vertoningsweek', '', 'ID'],
        '12_1946.csv': ['Bron', '', '', '', '', '', 'ID'],
        '12_1947.csv': ['Bron', '', '', '', '', '', 'ID'],
        '12_1948.csv': ['Bron', '', '', '', '', '', 'ID'],
        '12_1949.csv': ['Bron', '', '', '', '', '', 'ID'],
        '12_1950.csv': ['Bron', '', '', '', '', '', 'ID'],
        '12_1951.csv': ['Bron', '', '', '', '', '', 'ID'],
        '13_1945.csv': ['Bron titel 1', 'Bron titel 2', '', 'Bron datum 2', '', '', 'ID'],
        '13_1946.csv': ['Bron titel 1', 'Bron titel 2', '', '', '', '', 'ID'],
        '13_1947.csv': ['Bron titel 1', 'Bron titel 2', '', '', '', '', 'ID'],
        '13_1948.csv': ['Bron titel 1', 'Bron titel 2', '', '', '', '', 'ID'],
        '13_1949.csv': ['Bron titel 1', 'Bron titel 2', '', '', '', '', 'ID'],
        '13_1950.csv': ['Bron titel 1', 'Bron titel 2', 'Bron titel 3', '', '', '', 'ID'],
        '13_1951.csv': ['Bron titel 1', 'Bron titel 2', '', '', '', '', 'ID'],
        '13_1952_samengevoegd.csv': ['Bron titel 1', 'Bron titel 2', 'Bron titel 3', '', '', '', 'ID'],
        '13_1953.csv': ['Bron titel1', 'Bron titel 2', 'Bron titel 3', '', '', '', 'ID'],
        '13_1954.csv': ['Bron titel 1', 'Bron titel 2', 'Bron titel 3', '', '', '', 'ID'],
        '16.csv': ['Quelle', '', '', '', '', '', 'order_id'],
        '16_1.csv': ['Quelle', '', '', '', '', '', 'id'],
        '17_2000_2019.csv': ['', '', '', '', '', '', 'id'],
        '18.csv': ['REFCODE', '', '', '', '', '', 'order_id'],
        '19_1952a_films.csv': ['', '', '', 'Vertoningsweek', '', '', 'order_id'],
        '19_1952b_films.csv': ['', '', '', 'Vertoningsweek', '', '', 'order_id'],
        '19_1962a_films.csv': ['', '', '', 'Vertoningsweek', '', '', 'order_id'],
        '19_1962b_films.csv': ['', '', '', 'Vertoningsweek', '', '', 'order_id'],
        '19_1972_films.csv': ['', '', '', 'Vertoningsweek', '', '', 'order_id'],
    }
    for ds in ds_configs.keys():
        print(f'Processing {ds}')
        ds_config = ds_configs[ds]
        programming_sources[ds] = {}
        with open(f'data/clean/datasets/{ds}') as input_file:
            i_reader = csv.reader(input_file)

            i_header = next(i_reader)
            i_header_lookup = {h: i_header.index(h) for h in i_header}

            for row in i_reader:
                sources = []
                row_id = ds_config[-1]
                if ds == '09_4.csv':
                    sources.append('gva')
                elif '19_' in ds:
                    sources.append('gva')
                elif ds == '17_2000_2019.csv':
                    sources.append('van_beek')
                elif 'RAB/B13' in row[i_header_lookup[ds_config[0]]]:
                    sources.append(row[i_header_lookup[ds_config[0]]])
                elif ds in ['16.csv', '16_1.csv']:
                    sources = [s.strip() for s in row[i_header_lookup[ds_config[0]]].replace(' ; ', '|').split('|') if s not in ['', 'n/a']]
                elif ds == '18.csv':
                    sources.append(row[i_header_lookup[ds_config[0]]])
                else:
                    sources = [s.strip() for s in row[i_header_lookup[ds_config[0]]].split('/') if s not in ['', 'n/a']]

                    if ds_config[1] != '' and row[i_header_lookup[ds_config[1]]] not in ['', 'n/a']:
                        sources.append(row[i_header_lookup[ds_config[1]]].strip())

                    if ds_config[2] != '' and row[i_header_lookup[ds_config[2]]] not in ['', 'n/a']:
                        sources.append(row[i_header_lookup[ds_config[2]]].strip())

                if ds == '11.csv':
                    if row[i_header_lookup['Genre Krant']] != '':
                        if row[i_header_lookup['Bron_Genre_Krant']] == 'HLN':
                            sources.append('hln')
                        else:
                            sources.append('de gentenaar')

                date = ''
                if ds_config[3] != '':
                    date = row[i_header_lookup[ds_config[3]]]
                if date == '' and ds_config[4] != '':
                    date = row[i_header_lookup[ds_config[4]]]
                publication_date = ''
                if '12_' in ds:
                    publication_date = programme_dates[ds][row[i_header_lookup[row_id]]]
                elif date == 'XX/XX/1962':
                    publication_date = '1962-XX-XX'
                elif '193X' in date:
                    date = date.replace('193X', '1935')
                    publication_date = datetime.datetime.strftime(
                        datetime.datetime.strptime(
                            date,
                            '%m/%d/%Y'
                        ),
                        '%Y-%m-%d'
                    )
                    publication_date = publication_date.replace('1935', '193X')
                elif '19_' in ds:
                    date_parts = date.split('/')
                    publication_date = datetime.datetime.strftime(
                        datetime.datetime.strptime(
                            f'{date_parts[0].zfill(2)}/{date_parts[1].zfill(2)}/{date_parts[2]}',
                            '%m/%d/%Y'
                        ),
                        '%Y-%m-%d'
                    )
                elif len(date) == 10:
                    publication_date = datetime.datetime.strftime(
                        datetime.datetime.strptime(
                            date,
                            '%m/%d/%Y'
                        ),
                        '%Y-%m-%d'
                    )
                elif len(date) == 19:
                    publication_date = datetime.datetime.strftime(
                        datetime.datetime.strptime(
                            date,
                            '%m/%d/%Y 00:00:00'
                        ),
                        '%Y-%m-%d'
                    )

                source_props = {}
                if ds_config[5] != '' and row[i_header_lookup[ds_config[5]]] != '':
                    source_props['page_number'] = set([row[i_header_lookup[ds_config[5]]]])

                programming_sources[ds][row[i_header_lookup[row_id]]] = []

                source_found = False
                for source in sources:
                    if '13_' in ds and 'Vooruit,' in source:
                        source, date = source.split(', ')
                        publication_date = datetime.datetime.strftime(
                            datetime.datetime.strptime(
                                date,
                                '%Y%m%d'
                            ),
                            '%Y-%m-%d'
                        )
                    if ds == '16.csv' and 'SVZ ' in source:
                        source, date = source.split(' ', 1)
                        publication_date = datetime.datetime.strftime(
                            datetime.datetime.strptime(
                                date.strip(),
                                '%d/%m/%Y'
                            ),
                            '%Y-%m-%d'
                        )
                    if ds == '16.csv' and ('GE ' in source or 'GE, ' in source):
                        source, date = source.split(' ', 1)
                        source = source.replace(',', '')
                        if ', S.' in date:
                            date, page_number = date.split(', S.')
                            # Add 19 to year
                            date = f'{date[:6]}19{date[6:]}'
                            source_props['page_number'] = set([page_number])

                        publication_date = datetime.datetime.strftime(
                            datetime.datetime.strptime(
                                date.strip(),
                                '%d/%m/%Y'
                            ),
                            '%Y-%m-%d'
                        )
                    if ds == '16.csv' and 'LSE ' in source:
                        source, date = source.split(' ')
                        publication_date = datetime.datetime.strftime(
                            datetime.datetime.strptime(
                                date.strip(),
                                '%d/%m/%Y'
                            ),
                            '%Y-%m-%d'
                        )
                    if ds == '16.csv' and 'EN, ' in source:
                        source, date = source.split(' ', 1)
                        source = source.replace(',', '')
                        if ', S.' in date:
                            date, page_number = date.split(', S.')
                            # Add 19 to year
                            date = f'{date[:6]}19{date[6:]}'
                            source_props['page_number'] = set([page_number])

                        publication_date = datetime.datetime.strftime(
                            datetime.datetime.strptime(
                                date.strip(),
                                '%d/%m/%Y'
                            ),
                            '%Y-%m-%d'
                        )
                    if ds == '16.csv' and ('Korrespondenzblatt Eupen' in source or 'Eupener Zeitung' in source):
                        day, month, year = source.split(' ')[0:3]
                        # remove dot
                        day = day[:-1]
                        month = M[month.lower()]
                        publication_date = f'{year}-{month}-{day}'

                        if 'Korrespondenzblatt Eupen' in source:
                            source = 'Korrespondenzblatt Eupen'
                        else:
                            source = 'Eupener Zeitung'
                    if ds == '16_1.csv':
                        date = source.split(' ')[-1]
                        source = 'Die Fliegende Taube'
                        publication_date = datetime.datetime.strftime(
                            datetime.datetime.strptime(
                                date.strip(),
                                '%d.%m.%Y'
                            ),
                            '%Y-%m-%d'
                        )

                    if source.lower() == 'gva':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '0771-1581',
                                'title': 'Gazet van Antwerpen',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': 'Antwerpen',
                                'publisher': 'De Vlijt',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'de gentenaar':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '1378-8930',
                                'title': 'De Gentenaar',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': 'Gent',
                                'publisher': 'Van Overbeke-Gyselbrecht',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() in ['vooruit', 'de vooruit']:
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '',
                                'title': 'Vooruit',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': 'Gent',
                                'publisher': 'De nieuwe morgen',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'hln':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '1780-1273',
                                'title': 'Het Laatste Nieuws',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': 'Antwerpen',
                                'publisher': 'DPG Media',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'svz':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '',
                                'title': 'St. Vither Volkszeitung',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': 'Sankt Vith',
                                'publisher': 'Doepgen',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'ge':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '',
                                'title': 'Grenz-Echo',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': 'Eupen',
                                'publisher': 'Grenz-Echo Verlag',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'lse':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '',
                                'title': 'La Semaine',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': '',
                                'publisher': '',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'korrespondenzblatt eupen':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '',
                                'title': 'Korespondenzblatt Eupen',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': 'Eupen',
                                'publisher': 'Tilgenkamp, Gustav',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'eupener zeitung':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '',
                                'title': 'Eupener Zeitung',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': '',
                                'publisher': '',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'en':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '',
                                'title': 'Eupener Nachrichten',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': '',
                                'publisher': '',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source.lower() == 'die fliegende taube':
                        source_found = True
                        key = (
                            source.lower() +
                            '_' +
                            publication_date
                        )

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Newspaper',
                                'isbn': '',
                                'issn': '',
                                'title': 'Die Fliegende Taube',
                                'book_journal_title': '',
                                'publication_date': publication_date,
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': 'Aubel',
                                'publisher': 'Willems',
                                'start_page': '',
                                'end_page': '',
                                'url': '',
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif source in FILMPORTAL:
                        source_found = True
                        key = source

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Website',
                                'isbn': '',
                                'issn': '',
                                'title': FILMPORTAL[source],
                                'book_journal_title': '',
                                'publication_date': '',
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': '',
                                'publisher': 'filmportal.de',
                                'start_page': '',
                                'end_page': '',
                                'url': source,
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif 'filmportal' in source:
                        print('not in filmportal')
                        print(row)
                    elif source in EARLYCINEMA:
                        source_found = True
                        key = source

                        if key not in publication_lookup:
                            publication_id = str(len(publications) + 1)
                            publications.append({
                                'publication_id': publication_id,
                                'editorial_comment': '',
                                'digitally_available': '',
                                'publication_type': 'Website',
                                'isbn': '',
                                'issn': '',
                                'title': EARLYCINEMA[source],
                                'book_journal_title': '',
                                'publication_date': '',
                                'publication_volume': '',
                                'publication_number': '',
                                'author': '',
                                'editor': '',
                                'place': '',
                                'publisher': 'the German early cinema database ',
                                'start_page': '',
                                'end_page': '',
                                'url': source,
                            }.values())
                            publication_lookup[key] = publication_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', publication_lookup[key], source_props])
                    elif 'earlycinema' in source:
                        print('not in earlycinema')
                        print(row)
                    elif 'BE/942855/1927/' in source:
                        source_found = True
                        key = source

                        if key not in archive_item_lookup:
                            archive_item_id = str(len(archive_items) + 1)

                            teneo_id = row[i_header_lookup["TENEO_ID"]]
                            url = ''
                            if teneo_id != '':
                                url = f'https://resolver.libis.be/{teneo_id}/representation'

                            archive_items.append({
                                'id': archive_item_id,
                                'inventory_id': 'BE/942855/1927',
                                'inventory_description': 'Verzameling filmdossiers Katholieke Filmliga/Filmmagie, 1930-2000',
                                'item_number': row[i_header_lookup['REFCODE']],
                                'name': row[i_header_lookup['TITLE']],
                                'url': url,
                                'archive_id': '5',
                                'editorial_comment': '',
                            }.values())
                            archive_item_lookup[key] = archive_item_id

                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', archive_item_lookup[key], source_props, teneo_id])
                    elif source.lower() in ['programmeringsboeken', 'programmeringsboeken rex', 'rex programmaboeken']:
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '3', source_props])
                    elif source == 'RAB/B13 201':
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '4', source_props])
                    elif 'RAB/B13/' in source:
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '5', source_props])
                    elif source == 'Ontvangstborderellen\n Leopold. 1946 – 1954':
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '10', source_props])
                    elif source == '339_Ontvangsten, 1946 – 1948':
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '11', source_props])
                    elif 'SAE' in source:
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '12', source_props])
                    elif source == 'van_beek':
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['publication', '2', source_props])
                    else:
                        print('umatched source')
                        print(source)

                    if (
                        ds in ['12_1946.csv', '12_1947.csv', '12_1948.csv']
                        or (ds == '12_1949.csv' and publication_date != '1949-12-23')
                    ):
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '6', source_props])

                    if (
                        ds in ['12_1946.csv', '12_1947.csv']
                        or (ds == '12_1948.csv' and publication_date[5:7] in ['01', '02', '03', '04', '05', '06'])
                    ):
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '7', source_props])
                    elif (
                        ds == '12_1948.csv'
                        or (ds == '12_1949.csv' and publication_date != '1949-12-23')
                    ):
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '8', source_props])
                    elif ds in ['12_1949.csv', '12_1950.csv', '12_1951.csv']:
                        source_found = True
                        programming_sources[ds][row[i_header_lookup[row_id]]].append(['archive_item', '9', source_props])

                if not source_found:
                    print('No source found')
                    print(row)

    print('Linking sources')


    with open('data/original/source_links/tblFilmSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] == '18.csv':
                for source in programming_sources[row[i_header_lookup['dataset']]][row[i_header_lookup['row']]]:
                    add_source(
                        'film',
                        row[i_header_lookup['film_id']],
                        [f'filmmagie_id[{film_teneo[row[i_header_lookup["film_id"]]].index(source[3])}]'],
                        source[0],
                        source[1],
                        entity_sources,
                        source[2],
                    )


    with open('data/original/source_links/tblFilmTitleVariationSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ds_configs:
                for source in programming_sources[row[i_header_lookup['dataset']]][row[i_header_lookup['row']]]:
                    add_source(
                        'mentioned_film_title',
                        row[i_header_lookup['film_variation_id']],
                        ['title'],
                        source[0],
                        source[1],
                        entity_sources,
                        source[2],
                    )

    with open('data/original/source_links/tblJoinFilmCompanySource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ds_configs and '19_' not in row[i_header_lookup['dataset']]:
                for source in programming_sources[row[i_header_lookup['dataset']]][row[i_header_lookup['row']]]:
                    add_source(
                        'film_company',
                        row[i_header_lookup['film_company_id']],
                        ['__rel__', 'type'],
                        source[0],
                        source[1],
                        relation_sources,
                        source[2],
                    )

    with open('data/original/source_links/tblProgrammeSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ds_configs:
                for source in programming_sources[row[i_header_lookup['dataset']]][row[i_header_lookup['row']]]:
                    if source[0] == 'archive_item' and source[1] in ['5', '6', '7', '8', '9', '10', '11']:
                        add_source(
                            'programme',
                            row[i_header_lookup['programme_id']],
                            ['gross_income', 'number_of_tickets', 'mean_price', 'taxes_and_copyrights', 'net_income', 'cheapest_ticket', 'most_expensive_ticket'],
                            source[0],
                            source[1],
                            entity_sources,
                            source[2],
                        )
                    add_source(
                        'programme_venue',
                        row[i_header_lookup['programme_id']],
                        ['__rel__'],
                        source[0],
                        source[1],
                        relation_sources,
                        source[2],
                    )

    with open('data/original/source_links/tblProgrammeItemSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ds_configs:
                for source in programming_sources[row[i_header_lookup['dataset']]][row[i_header_lookup['row']]]:
                    add_source(
                        'programme_item',
                        row[i_header_lookup['programme_item_id']],
                        ['mentioned_venue', 'official_rating', 'catholic_rating', 'catholic_rating_extra'],
                        source[0],
                        source[1],
                        entity_sources,
                        source[2],
                    )
                    add_source(
                        'programme_programme_item',
                        row[i_header_lookup['programme_item_id']],
                        ['__rel__'],
                        source[0],
                        source[1],
                        relation_sources,
                        source[2],
                    )
                    add_source(
                        'programme_item_film',
                        row[i_header_lookup['programme_item_id']],
                        ['__rel__'],
                        source[0],
                        source[1],
                        relation_sources,
                        source[2],
                    )
                    if row[i_header_lookup['programme_item_id']] in programme_item_mentioned_titles:
                        for programme_item_mentioned_titles_id in programme_item_mentioned_titles[row[i_header_lookup['programme_item_id']]]:
                            add_source(
                                'programme_item_mentioned_film_title',
                                programme_item_mentioned_titles_id,
                                ['__rel__'],
                                source[0],
                                source[1],
                                relation_sources,
                                source[2],
                            )

    with open('data/original/source_links/tblProgrammeDateSource.csv') as input_file:
        i_reader = csv.reader(input_file)

        i_header = next(i_reader)
        i_header_lookup = {h: i_header.index(h) for h in i_header}

        for row in i_reader:
            if row[i_header_lookup['dataset']] in ds_configs:
                for source in programming_sources[row[i_header_lookup['dataset']]][row[i_header_lookup['row']]]:
                    add_source(
                        'programme_date',
                        row[i_header_lookup['programme_date_id']],
                        ['date_start', 'date_end', 'dates_mentioned'],
                        source[0],
                        source[1],
                        entity_sources,
                        source[2],
                    )
                    add_source(
                        'programme_programme_date',
                        row[i_header_lookup['programme_date_id']],
                        ['__rel__'],
                        source[0],
                        source[1],
                        relation_sources,
                        source[2],
                    )


    ##########################
    # Write sources to file  #
    ##########################

    print('Writing sources to file')

    with open('data/clean/tblPublication.csv') as input_file,\
            open('data/processed/tblPublication.csv', 'w') as output_file:
        i_reader = csv.reader(input_file)
        o_writer = csv.writer(output_file, lineterminator='\n')

        i_header = next(i_reader)
        o_writer.writerow(i_header)

        for publication in publications:
            o_writer.writerow(publication)

            publication_type = list(publication)[3]
            if publication_type != '' and publication_type not in publication_type_lookup:
                publication_type_id = str(len(publication_type_lookup) + 1)
                publication_type_lookup[publication_type] = publication_type_id

    with open('data/clean/tblPublicationType.csv') as input_file,\
            open('data/processed/tblPublicationType.csv', 'w') as output_file:
        i_reader = csv.reader(input_file)
        o_writer = csv.writer(output_file, lineterminator='\n')

        i_header = next(i_reader)
        o_writer.writerow(i_header)

        for type, id in publication_type_lookup.items():
            o_writer.writerow([id, type])

    with open('data/clean/tblArchive.csv') as input_file,\
            open('data/processed/tblArchive.csv', 'w') as output_file:
        i_reader = csv.reader(input_file)
        o_writer = csv.writer(output_file, lineterminator='\n')

        i_header = next(i_reader)
        o_writer.writerow(i_header)

        for archive in archives:
            o_writer.writerow(archive)

    with open('data/clean/tblArchiveItem.csv') as input_file,\
            open('data/processed/tblArchiveItem.csv', 'w') as output_file:
        i_reader = csv.reader(input_file)
        o_writer = csv.writer(output_file, lineterminator='\n')

        i_header = next(i_reader)
        o_writer.writerow(i_header)

        for archive_item in archive_items:
            o_writer.writerow(archive_item)


    write_sources(
        'data/processed/entity_sources.csv',
        ['entity_type', 'entity_id', 'properties', 'source_type', 'source_id', 'source_props'],
        entity_sources,
    )

    write_sources(
        'data/processed/relation_sources.csv',
        ['relation_type', 'relation_id', 'properties', 'source_type', 'source_id', 'source_props'],
        relation_sources,
    )


if __name__ == '__main__':
    typer.run(main)
