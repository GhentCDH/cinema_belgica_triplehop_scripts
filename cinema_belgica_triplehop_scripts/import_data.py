import asyncio
import time
import typing

import asyncpg
import config
import typer
from triplehop_import_tools import db_data, db_structure


async def create_structure(structure_actions: typing.List[str]):
    pool = await asyncpg.create_pool(**config.DATABASE)

    if not structure_actions or "project_config" in structure_actions:
        await db_structure.create_project_config(
            pool=pool,
            system_name="cinema_belgica",
            display_name="Cinema Belgica",
            username="cinema_belgica",
        )

    if not structure_actions or "entity_configs" in structure_actions:
        entities_types = {
            "film": "Film",
            "mentioned_film_title": "Mentioned film title",
            "continent": "Continent",
            "country": "Country",
            "city": "City",
            "address": "Address",
            "venue": "Venue",
            "person": "Person",
            "company": "Company",
            "company_name": "Company name",
            "programme": "Programme",
            "programme_date": "Programme date",
            "programme_item": "Programme item",
            "film_episode": "Film episode",
            "censorship_cut_main_category": "Censorship main category",
            "censorship_cut_detailed_category": "Censorship detailed category",
            "censorship": "Censorship",
            "censorship_cut": "Censorship cut",
            "archive": "Archive",
            "archive_item": "Archive item",
            "publication_type": "Publication type",
            "publication": "Publication",
        }
        for (system_name, display_name) in entities_types.items():
            await db_structure.create_entity_config(
                pool=pool,
                project_name="cinema_belgica",
                username="cinema_belgica",
                system_name=system_name,
                display_name=display_name,
                config=db_structure.read_config_from_file(
                    type="entity",
                    system_name=system_name,
                ),
            )

    if not structure_actions or "relation_configs" in structure_actions:
        relation_types = {
            "mentioned_film_title": [
                "Mentioned Film Title",
                ["film"],
                ["mentioned_film_title"],
            ],
            "country_continent": ["Continent", ["country"], ["continent"]],
            "film_country": ["Film Country", ["film"], ["country"]],
            "address_city": ["City", ["address"], ["city"]],
            "address": ["Address", ["venue", "archive"], ["address"]],
            "film_person": ["Film Person", ["film"], ["person"]],
            "venue_person": ["Venue Person", ["venue"], ["person"]],
            "company_name": ["Company Name", ["company"], ["company_name"]],
            "company_company": ["Subsidiary", ["company"], ["company"]],
            "company_person": ["Company Person", ["company"], ["person"]],
            "film_company": ["Film Company", ["film"], ["company"]],
            "venue_company": ["Venue Company", ["venue"], ["company"]],
            "programme_programme_date": [
                "Programme date",
                ["programme"],
                ["programme_date"],
            ],
            "programme_programme_item": [
                "Programme item",
                ["programme"],
                ["programme_item"],
            ],
            "programme_item_film": ["Film", ["programme_item"], ["film"]],
            "programme_item_mentioned_film_title": [
                "Mentioned film title",
                ["programme_item"],
                ["mentioned_film_title"],
            ],
            "programme_venue": ["Venue", ["programme"], ["venue"]],
            "episode_film": ["Film", ["film_episode"], ["film"]],
            "censorship_cut_main_category": [
                "Censorship Main Category",
                ["censorship_cut_detailed_category"],
                ["censorship_cut_main_category"],
            ],
            "film_censorship": ["Censorship", ["film"], ["censorship"]],
            "episode_censorship": ["Censorship", ["film_episode"], ["censorship"]],
            "censorship_appeal": ["Appeal", ["censorship"], ["censorship"]],
            "censorship_cut": ["Censorship cut", ["censorship"], ["censorship_cut"]],
            "censorship_cut_category": [
                "Censorship cut category",
                ["censorship_cut"],
                ["censorship_cut_detailed_category"],
            ],
            "archive_item_archive": ["Archive", ["archive_item"], ["archive"]],
            "publication_publication_type": [
                "Publication type",
                ["publication"],
                ["publication_type"],
            ],
        }
        for (system_name, (display_name, domains, ranges)) in relation_types.items():
            await db_structure.create_relation_config(
                pool=pool,
                project_name="cinema_belgica",
                username="cinema_belgica",
                system_name=system_name,
                display_name=display_name,
                config=db_structure.read_config_from_file(
                    type="relation",
                    system_name=system_name,
                ),
                domains=domains,
                ranges=ranges,
            )
        await db_structure.create_relation_config(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            system_name="_source_",
            display_name="Source",
            config="{}",
            domains=[],
            ranges=[],
        )

    if not structure_actions or "recreate_graph" in structure_actions:
        print("Dropping existing graph and creating a new one")
        await db_structure.drop_project_graph(pool, "cinema_belgica")
        await db_structure.create_project_graph(pool, "cinema_belgica")

    await pool.close()


async def create_data(data_actions: typing.List[str] = None):
    pool = await asyncpg.create_pool(**config.DATABASE)

    # property -> nid lookups to improve performance
    lookups: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]] = {}

    if not data_actions or "entity__film" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblFilm.csv",
                "entity_type_name": "film",
                "props": {
                    "id": ["int", "film_id"],
                    "title": ["string", "title"],
                    "year": ["int", "film_year"],
                    "imdb_id": ["string", "imdb"],
                    "wikidata_id": ["string", "wikidata"],
                    "filmmagie_id": ["[string]", "kadoc_id", "|"],
                    "length": ["string", "film_length"],
                    "length_unit": ["string", "film_length_unit"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__mentioned_film_title" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblFilmTitleVariation.csv",
                "entity_type_name": "mentioned_film_title",
                "props": {
                    "id": ["int", "film_variation_id"],
                    "title": ["string", "title"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__person" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblPersonWithFirstNames.csv",
                "entity_type_name": "person",
                "props": {
                    "id": ["int", "person_id"],
                    "first_names": ["[string]", "first_names", "|"],
                    "last_name": ["string", "last_name"],
                    "suffix": ["string", "suffix"],
                    "name": ["string", "name"],
                    "info": ["string", "info"],
                    "imdb_id": ["string", "imdb"],
                    "wikidata_id": ["string", "wikidata"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__continent" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblContinent.csv",
                "entity_type_name": "continent",
                "props": {
                    "id": ["int", "continent_id"],
                    "original_id": ["string", "code"],
                    "name": ["string", "name"],
                },
            },
            lookups=lookups,
            lookup_props=["id", "original_id"],
        )

    if not data_actions or "entity__country" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblCountry.csv",
                "entity_type_name": "country",
                "props": {
                    "id": ["int", "country_id"],
                    "original_id": ["string", "code"],
                    "name": ["string", "name"],
                },
            },
            lookups=lookups,
            lookup_props=["id", "original_id"],
        )

    if not data_actions or "entity__city" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCity.csv",
                "entity_type_name": "city",
                "props": {
                    "id": ["int", "id"],
                    "name": ["string", "name"],
                    "postal_code": ["int", "postal_code"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__address" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblAddressWithGeoJson.csv",
                "entity_type_name": "address",
                "props": {
                    "id": ["int", "sequential_id"],
                    "original_id": ["string", "address_id"],
                    "street_name": ["string", "street_name"],
                    "location": ["geometry", "geodata"],
                    "district": ["string", "info"],
                    "architectural_info": ["string", "architectural_info"],
                },
            },
            lookups=lookups,
            lookup_props=["id", "original_id"],
        )

    if not data_actions or "entity__venue" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblVenueWithScreensAndSeats.csv",
                "entity_type_name": "venue",
                "props": {
                    "id": ["int", "sequential_id"],
                    "original_id": ["string", "venue_id"],
                    "name": ["string", "name"],
                    "date_opened": ["edtf", "date_opened"],
                    "date_closed": ["edtf", "date_closed"],
                    "status": ["string", "status"],
                    "type": ["string", "type"],
                    "ideological_characteristic": [
                        "string",
                        "ideological_characteristic",
                    ],
                    "ideological_remark": ["string", "ideological_remark"],
                    "infrastructure_info": ["string", "infrastructure_info"],
                    "name_remarks": ["string", "name_remarks"],
                    "screens": ["string", "screens"],
                    "seats": ["string", "seats"],
                },
            },
            lookups=lookups,
            lookup_props=["id", "original_id"],
        )

    if not data_actions or "entity__company" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblCompany.csv",
                "entity_type_name": "company",
                "props": {
                    "id": ["int", "company_id"],
                    "name": ["string", "name"],
                    "date_start": ["edtf", "date_established"],
                    "date_end": ["edtf", "date_disbanded"],
                    "info": ["string", "info"],
                    "nature": ["string", "nature"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__company_name" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCompanyNamesSplitDates.csv",
                "entity_type_name": "company_name",
                "props": {
                    "id": ["int", "sequential_id"],
                    "name": ["string", "name"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__programme" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblProgrammeWithImagesAndBoxOffice.csv",
                "entity_type_name": "programme",
                "props": {
                    "id": ["int", "programme_id"],
                    "vooruit_image": ["string", "vooruit_image_url"],
                    "gross_income": ["string", "gross_income"],
                    "number_of_tickets": ["string", "number_of_tickets"],
                    "mean_price": ["string", "mean_price"],
                    "taxes_and_copyrights": ["string", "taxes_and_copyrights"],
                    "net_income": ["string", "net_income"],
                    "cheapest_ticket": ["string", "cheapest_ticket"],
                    "most_expensive_ticket": ["string", "most_expensive_ticket"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__programme_date" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblProgrammeDateCalculated.csv",
                "entity_type_name": "programme_date",
                "props": {
                    "id": ["int", "programme_date_id"],
                    "date_start": ["edtf", "date_start"],
                    "date_end": ["edtf", "date_end"],
                    "dates_mentioned": ["[string]", "dates_mentioned", "|"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__programme_item" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblProgrammeItem.csv",
                "entity_type_name": "programme_item",
                "props": {
                    "id": ["int", "programme_item_id"],
                    "mentioned_venue": ["string", "info"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__film_episode" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblFilmEpisode.csv",
                "entity_type_name": "film_episode",
                "props": {
                    "id": ["int", "episode_id"],
                    "title": ["string", "title"],
                    "year": ["int", "episode_year"],
                    "length": ["string", "episode_length"],
                    "length_unit": ["string", "episode_length_unit"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__censorship_cut_main_category" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCensorshipCutMainCategory.csv",
                "entity_type_name": "censorship_cut_main_category",
                "props": {
                    "id": ["int", "id"],
                    "code": ["string", "code"],
                    "name": ["string", "name_en"],
                },
            },
            lookups=lookups,
            lookup_props=["id", "code"],
        )

    if not data_actions or "entity__censorship_cut_detailed_category" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCensorshipCutDetailedCategory.csv",
                "entity_type_name": "censorship_cut_detailed_category",
                "props": {
                    "id": ["int", "id"],
                    "code": ["string", "code"],
                    "name": ["string", "name_en"],
                },
            },
            lookups=lookups,
            lookup_props=["id", "code"],
        )

    if not data_actions or "entity__censorship" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCensorship.csv",
                "entity_type_name": "censorship",
                "props": {
                    "id": ["int", "censorship_id"],
                    "rating": ["string", "rating"],
                    "date": ["edtf", "date"],
                    "motivation": ["string", "motivation"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__censorship_cut" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblCensorshipCut.csv",
                "entity_type_name": "censorship_cut",
                "props": {
                    "id": ["int", "cut_id"],
                    "date": ["edtf", "cut_date"],
                    "comment_nl": ["string", "comment_by_censor_nl"],
                    "comment_fr": ["string", "comment_by_censor_fr"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__archive" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblArchive.csv",
                "entity_type_name": "archive",
                "props": {
                    "id": ["int", "id"],
                    "name": ["string", "name"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__archive_item" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblArchiveItem.csv",
                "entity_type_name": "archive_item",
                "props": {
                    "id": ["int", "id"],
                    "editorial_comment": ["string", "editorial_comment"],
                    "inventory_id": ["string", "inventory_id"],
                    "inventory_description": ["string", "inventory_description"],
                    "item_number": ["string", "item_number"],
                    "name": ["string", "name"],
                    "url": ["string", "url"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "entity__publication_type" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblPublicationType.csv",
                "entity_type_name": "publication_type",
                "props": {
                    "id": ["int", "id"],
                    "type": ["string", "type"],
                },
            },
            lookups=lookups,
            lookup_props=["id", "type"],
        )

    if not data_actions or "entity__publication" in data_actions:
        await db_data.import_entities(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblPublication.csv",
                "entity_type_name": "publication",
                "props": {
                    "id": ["int", "publication_id"],
                    "editorial_comment": ["string", "editorial_comment"],
                    "title": ["string", "title"],
                    "url": ["string", "url"],
                    "publication_date": ["edtf", "publication_date"],
                    "publication_volume": ["string", "publication_volume"],
                    "publication_number": ["string", "publication_number"],
                    "authors": ["[string]", "author", "|"],
                    "editors": ["[string]", "editor", "|"],
                    "place": ["string", "place"],
                    "publisher": ["string", "publisher"],
                    "start_page": ["string", "start_page"],
                    "end_page": ["string", "end_page"],
                },
            },
            lookups=lookups,
            lookup_props=["id"],
        )

    if not data_actions or "relation__mentioned_film_title" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblFilmTitleVariation.csv",
                "relation_type_name": "mentioned_film_title",
                "domain_type_name": "film",
                "range_type_name": "mentioned_film_title",
                "domain": {
                    "id": ["int", "film_id"],
                },
                "range": {
                    "id": ["int", "film_variation_id"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    if not data_actions or "relation__country_continent" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblCountry.csv",
                "relation_type_name": "country_continent",
                "domain_type_name": "country",
                "range_type_name": "continent",
                "domain": {
                    "id": ["int", "country_id"],
                },
                "range": {
                    "original_id": ["string", "continent_code"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    if not data_actions or "relation__film_country" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblFilm.csv",
                "relation_type_name": "film_country",
                "domain_type_name": "film",
                "range_type_name": "country",
                "domain": {
                    "id": ["int", "film_id"],
                },
                "range": {
                    "original_id": ["string", "country"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    if not data_actions or "relation__address_city" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblJoinAddressCity.csv",
                "relation_type_name": "address_city",
                "domain_type_name": "address",
                "range_type_name": "city",
                "domain": {
                    "original_id": ["string", "address_id"],
                },
                "range": {
                    "id": ["int", "city_id"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    if not data_actions or "relation__film_person" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblJoinFilmPerson.csv",
                "relation_type_name": "film_person",
                "domain_type_name": "film",
                "range_type_name": "person",
                "domain": {
                    "id": ["int", "film_id"],
                },
                "range": {
                    "id": ["int", "person_id"],
                },
                "props": {
                    "type": ["string", "info"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__venue_address" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblVenue.csv",
                "relation_type_name": "address",
                "domain_type_name": "venue",
                "range_type_name": "address",
                "domain": {
                    "original_id": ["string", "venue_id"],
                },
                "range": {
                    "original_id": ["string", "address_id"],
                },
                "props": {
                    "id": ["int", "sequential_id"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__venue_person" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblJoinVenuePerson.csv",
                "relation_type_name": "venue_person",
                "domain_type_name": "venue",
                "range_type_name": "person",
                "domain": {
                    "original_id": ["string", "venue_id"],
                },
                "range": {
                    "id": ["int", "person_id"],
                },
                "props": {
                    "type": ["string", "job_type"],
                    "date_start": ["edtf", "start_date"],
                    "date_end": ["edtf", "end_date"],
                    "years": ["string", "years"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__company_name" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCompanyNamesSplitDates.csv",
                "relation_type_name": "company_name",
                "domain_type_name": "company",
                "range_type_name": "company_name",
                "domain": {
                    "id": ["int", "company_id"],
                },
                "range": {
                    "id": ["int", "sequential_id"],
                },
                "props": {
                    "date_start": ["edtf", "date_start"],
                    "date_end": ["edtf", "date_end"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__company_company" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblJoinCompanyCompany.csv",
                "relation_type_name": "company_company",
                "domain_type_name": "company",
                "range_type_name": "company",
                "domain": {
                    "id": ["int", "company_id"],
                },
                "range": {
                    "id": ["int", "subsidiary_id"],
                },
                "props": {
                    "subsidiary_type": ["string", "subsidiary_type"],
                    "date_start": ["edtf", "start_date"],
                    "date_end": ["edtf", "end_date"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__company_person" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblJoinCompanyPerson.csv",
                "relation_type_name": "company_person",
                "domain_type_name": "company",
                "range_type_name": "person",
                "domain": {
                    "id": ["int", "company_id"],
                },
                "range": {
                    "id": ["int", "person_id"],
                },
                "props": {
                    "type": ["string", "job_type"],
                    "date_start": ["edtf", "start_date"],
                    "date_end": ["edtf", "end_date"],
                    "years": ["string", "years"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__film_company" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblJoinFilmCompany.csv",
                "relation_type_name": "film_company",
                "domain_type_name": "film",
                "range_type_name": "company",
                "domain": {
                    "id": ["int", "film_id"],
                },
                "range": {
                    "id": ["int", "company_id"],
                },
                "props": {
                    "id": ["int", "film_company_id"],
                    "type": ["string", "info"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__venue_company" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblJoinVenueCompany.csv",
                "relation_type_name": "venue_company",
                "domain_type_name": "venue",
                "range_type_name": "company",
                "domain": {
                    "original_id": ["string", "venue_id"],
                },
                "range": {
                    "id": ["int", "company_id"],
                },
                "props": {
                    "type": ["string", "info"],
                    "date_start": ["edtf", "start_date"],
                    "date_end": ["edtf", "end_date"],
                    "years": ["string", "years"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__programme_programme_date" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblProgrammeDateCalculated.csv",
                "relation_type_name": "programme_programme_date",
                "domain_type_name": "programme",
                "range_type_name": "programme_date",
                "domain": {
                    "id": ["int", "programme_id"],
                },
                "range": {
                    "id": ["int", "programme_date_id"],
                },
                "props": {
                    "id": ["int", "programme_date_id"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__programme_programme_item" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblProgrammeItem.csv",
                "relation_type_name": "programme_programme_item",
                "domain_type_name": "programme",
                "range_type_name": "programme_item",
                "domain": {
                    "id": ["int", "programme_id"],
                },
                "range": {
                    "id": ["int", "programme_item_id"],
                },
                "props": {
                    "id": ["int", "programme_item_id"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__programme_item_film" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblProgrammeItem.csv",
                "relation_type_name": "programme_item_film",
                "domain_type_name": "programme_item",
                "range_type_name": "film",
                "domain": {
                    "id": ["int", "programme_item_id"],
                },
                "range": {
                    "id": ["int", "film_id"],
                },
                "props": {
                    "id": ["int", "programme_item_id"],
                },
            },
            lookups=lookups,
        )

    if (
        not data_actions
        or "relation__programme_item_mentioned_film_title" in data_actions
    ):
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblJoinProgrammeItemMentionedTitle.csv",
                "relation_type_name": "programme_item_mentioned_film_title",
                "domain_type_name": "programme_item",
                "range_type_name": "mentioned_film_title",
                "domain": {
                    "id": ["int", "programme_item_id"],
                },
                "range": {
                    "id": ["int", "mentioned_title_id"],
                },
                "props": {
                    "id": ["int", "programme_item_mentioned_title_id"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__programme_venue" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblProgrammeWithImagesAndBoxOffice.csv",
                "relation_type_name": "programme_venue",
                "domain_type_name": "programme",
                "range_type_name": "venue",
                "domain": {
                    "id": ["int", "programme_id"],
                },
                "range": {
                    "original_id": ["string", "venue_id"],
                },
                "props": {
                    "id": ["int", "programme_id"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__episode_film" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblFilmEpisode.csv",
                "relation_type_name": "episode_film",
                "domain_type_name": "film_episode",
                "range_type_name": "film",
                "domain": {
                    "id": ["int", "episode_id"],
                },
                "range": {
                    "id": ["int", "film_id"],
                },
                "props": {
                    "number": ["int", "info"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__censorship_cut_main_category" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCensorshipCutDetailedCategory.csv",
                "relation_type_name": "censorship_cut_main_category",
                "domain_type_name": "censorship_cut_detailed_category",
                "range_type_name": "censorship_cut_main_category",
                "domain": {
                    "code": ["string", "code"],
                },
                "range": {
                    "code": ["string", "main_code"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    if not data_actions or "relation__film_censorship" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCensorship.csv",
                "relation_type_name": "film_censorship",
                "domain_type_name": "film",
                "range_type_name": "censorship",
                "domain": {
                    "id": ["int", "film_id"],
                },
                "range": {
                    "id": ["int", "censorship_id"],
                },
                "props": {
                    "id": ["int", "censorship_id"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__episode_censorship" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCensorship.csv",
                "relation_type_name": "episode_censorship",
                "domain_type_name": "film_episode",
                "range_type_name": "censorship",
                "domain": {
                    "id": ["int", "episode_id"],
                },
                "range": {
                    "id": ["int", "censorship_episode_id"],
                },
                "props": {
                    "id": ["int", "censorship_episode_id"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__censorship_appeal" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblCensorship.csv",
                "relation_type_name": "censorship_appeal",
                "domain_type_name": "censorship",
                "range_type_name": "censorship",
                "domain": {
                    "id": ["int", "censorship_id"],
                },
                "range": {
                    "id": ["int", "censorship_appeal_id"],
                },
                "props": {
                    "id": ["int", "censorship_appeal_id"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__censorship_cut" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblCensorshipCut.csv",
                "relation_type_name": "censorship_cut",
                "domain_type_name": "censorship",
                "range_type_name": "censorship_cut",
                "domain": {
                    "id": ["int", "censorship_id"],
                },
                "range": {
                    "id": ["int", "cut_id"],
                },
                "props": {
                    "order": ["int", "s_order"],
                },
            },
            lookups=lookups,
        )

    if not data_actions or "relation__censorship_cut_category" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "clean/tblCensorshipCutCategory.csv",
                "relation_type_name": "censorship_cut_category",
                "domain_type_name": "censorship_cut",
                "range_type_name": "censorship_cut_detailed_category",
                "domain": {
                    "id": ["int", "cut_id"],
                },
                "range": {
                    "code": ["string", "category_code"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    if not data_actions or "relation__archive_address" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblArchive.csv",
                "relation_type_name": "address",
                "domain_type_name": "archive",
                "range_type_name": "address",
                "domain": {
                    "id": ["int", "id"],
                },
                "range": {
                    "id": ["int", "address_id"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    if not data_actions or "relation__archive_item_archive" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblArchiveItem.csv",
                "relation_type_name": "archive_item_archive",
                "domain_type_name": "archive_item",
                "range_type_name": "archive",
                "domain": {
                    "id": ["int", "id"],
                },
                "range": {
                    "id": ["int", "archive_id"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    if not data_actions or "relation__publication_publication_type" in data_actions:
        await db_data.import_relations(
            pool=pool,
            project_name="cinema_belgica",
            username="cinema_belgica",
            conf={
                "filename": "processed/tblPublication.csv",
                "relation_type_name": "publication_publication_type",
                "domain_type_name": "publication",
                "range_type_name": "publication_type",
                "domain": {
                    "id": ["int", "publication_id"],
                },
                "range": {
                    "type": ["string", "publication_type"],
                },
                "props": {},
            },
            lookups=lookups,
        )

    await pool.close()


async def create_sources(source_actions: typing.List[str] = None):
    pool = await asyncpg.create_pool(**config.DATABASE)

    await pool.close()


def main(
    actions: typing.List[str] = typer.Option(
        None, help="create_structure or create_data"
    ),
    sub_actions: typing.List[str] = typer.Option(None),
):
    start_time = time.time()
    loop = asyncio.get_event_loop()
    if not actions or "create_structure" in actions:
        loop.run_until_complete(create_structure(sub_actions))
    if not actions or "create_data" in actions:
        loop.run_until_complete(create_data(sub_actions))
    if not actions or "create_sources" in actions:
        loop.run_until_complete(create_sources(sub_actions))
    loop.close()
    print(f"Total time: {time.time() - start_time}")


if __name__ == "__main__":
    typer.run(main)
