import asyncio
import csv
import json
import time
import typing

import asyncpg
import config
import typer
from triplehop_import_tools import db_base, db_structure


async def get_entities_props(
    pool: asyncpg.pool.Pool,
    project_name: str,
) -> typing.Dict[str, typing.Dict]:
    records = await db_base.fetch(
        pool,
        """
            SELECT entity.id, entity.system_name, entity.config
            FROM app.entity
            INNER JOIN app.project
                ON entity.project_id = project.id
            WHERE project.system_name = :project_name
        """,
        {
            "project_name": project_name,
        },
    )

    results = {}
    for record in records:
        config = json.loads(record["config"])
        if not "data" in config:
            continue
        if not "fields" in config["data"]:
            continue
        result = {}
        for field, field_data in config["data"]["fields"].items():
            result[field] = field_data["system_name"]
        results[record["system_name"]] = {
            "id": str(record["id"]),
            "props": result,
        }

    return results


async def get_entities(
    pool: asyncpg.pool.Pool,
    project_name: str,
    entity_type_id: str,
    props_config: typing.Dict[str, str],
) -> typing.List[typing.Dict]:
    project_id = await db_structure.get_project_id(pool, project_name)
    records = await db_base.fetch(
        pool,
        (
            f"SELECT * FROM cypher("
            f"'{project_id}', "
            f"$$MATCH"
            f"    (n:n_{db_base.dtu(entity_type_id)}) "
            f"WITH n "
            f"ORDER BY n.id "
            f"return n$$"
            f") as (n agtype);"
        ),
        {},
        True,
    )
    results = []
    for record in records:
        raw_data = json.loads(record["n"][:-8])["properties"]
        result = {
            "id": raw_data["id"],
        }
        for prop_id, prop_name in props_config.items():
            if prop_name == "original_id":
                continue
            p_id = f"p_{db_base.dtu(prop_id)}"
            if p_id not in raw_data:
                continue
            result[prop_name] = raw_data[p_id]
        results.append(result)
    return results


async def get_relations_props(
    pool: asyncpg.pool.Pool,
    project_name: str,
) -> typing.Dict[str, typing.Dict]:
    records = await db_base.fetch(
        pool,
        """
            SELECT relation.id, relation.system_name, relation.config
            FROM app.relation
            INNER JOIN app.project
                ON relation.project_id = project.id
            WHERE project.system_name = :project_name
        """,
        {
            "project_name": project_name,
        },
    )

    results = {}
    for record in records:
        config = json.loads(record["config"])
        if not "data" in config:
            continue
        if not "fields" in config["data"]:
            continue
        result = {}
        for field, field_data in config["data"]["fields"].items():
            result[field] = field_data["system_name"]
        results[record["system_name"]] = {
            "id": str(record["id"]),
            "props": result,
        }

    return results


async def get_relations(
    pool: asyncpg.pool.Pool,
    project_name: str,
    relation_type_id: str,
    props_config: typing.Dict[str, str],
    entity_type_lookup: typing.Dict[str, str],
) -> typing.List[typing.Dict]:
    project_id = await db_structure.get_project_id(pool, project_name)
    records = await db_base.fetch(
        pool,
        (
            f"SELECT * FROM cypher("
            f"'{project_id}', "
            f"$$MATCH"
            f"    (d)-[e:e_{db_base.dtu(relation_type_id)}]->(r) "
            f"return d, e, r$$"
            f") as (d agtype, e agtype, r agtype);"
        ),
        {},
        True,
    )
    results = []
    for record in records:
        domain_data = json.loads(record["d"][:-8])
        range_data = json.loads(record["r"][:-8])

        edge_props = json.loads(record["e"][:-6])["properties"]
        edge_result = {
            "id": edge_props["id"],
        }
        for prop_id, prop_name in props_config.items():
            p_id = f"p_{db_base.dtu(prop_id)}"
            if p_id not in edge_props:
                continue
            edge_result[prop_name] = edge_props[p_id]

        results.append(
            {
                "domain_entity_type": entity_type_lookup[domain_data["label"]],
                "domain_id": domain_data["properties"]["id"],
                "range_entity_type": entity_type_lookup[range_data["label"]],
                "range_id": range_data["properties"]["id"],
                "edge": edge_result,
            }
        )

    return sorted(results, key=lambda x: x["edge"]["id"])


async def export_data():
    pool = await asyncpg.create_pool(**config.DATABASE)

    entities_props = await get_entities_props(
        pool=pool,
        project_name="cinema_belgica",
    )
    for entity_type_name, entity_config in entities_props.items():
        # Prepend id, add all props except for original_id
        columns = [
            "id",
            *[v for v in entity_config["props"].values() if v != "original_id"],
        ]
        with open(f"export/entities/{entity_type_name}.csv", "w") as out_file:
            out_writer = csv.DictWriter(
                out_file,
                fieldnames=columns,
                lineterminator="\n",
            )
            out_writer.writeheader()

            data = await get_entities(
                pool=pool,
                project_name="cinema_belgica",
                entity_type_id=entity_config["id"],
                props_config=entity_config["props"],
            )
            for row in data:
                out_writer.writerow(row)

    relation_props = await get_relations_props(
        pool=pool,
        project_name="cinema_belgica",
    )
    entity_type_lookup = {
        f"n_{db_base.dtu(entity_config['id'])}": entity_type_name
        for entity_type_name, entity_config in entities_props.items()
    }

    relation_lookup = {}
    for relation_type_name, relation_config in relation_props.items():
        print(relation_type_name)
        relation_lookup[relation_type_name] = {}

        data = await get_relations(
            pool=pool,
            project_name="cinema_belgica",
            relation_type_id=relation_config["id"],
            props_config=relation_config["props"],
            entity_type_lookup=entity_type_lookup,
        )

        domain_entity_types = set()
        range_entity_types = set()

        for row in data:
            domain_entity_types.add(row["domain_entity_type"])
            range_entity_types.add(row["range_entity_type"])

        for domain_entity_type in domain_entity_types:
            for range_entity_type in range_entity_types:
                # Prepend ids, add relation props
                columns = [
                    "relation_id",
                    f"{domain_entity_type}_id",
                    f"{range_entity_type}_id",
                    *[v for v in relation_config["props"].values()],
                ]
                with open(
                    f"export/relations/{domain_entity_type}__{range_entity_type}.csv",
                    "w",
                ) as out_file:
                    out_writer = csv.DictWriter(
                        out_file,
                        fieldnames=columns,
                        lineterminator="\n",
                    )
                    out_writer.writeheader()

                    for row in data:
                        if row["domain_entity_type"] != domain_entity_type:
                            continue
                        if row["range_entity_type"] != range_entity_type:
                            continue

                        relation_lookup[relation_type_name][
                            row["edge"]["id"]
                        ] = f"{domain_entity_type}__{range_entity_type}"

                        out_writer.writerow(
                            {
                                "relation_id": row["edge"]["id"],
                                f"{domain_entity_type}_id": row["domain_id"],
                                f"{range_entity_type}_id": row["range_id"],
                                **{k: v for k, v in row["edge"].items() if k != "id"},
                            }
                        )

    with open("data/processed/entity_sources.csv") as in_file:
        in_reader = csv.DictReader(in_file)

        data = {}
        for row in in_reader:
            entity_type = row["entity_type"]
            source_type = row["source_type"]

            if entity_type not in data:
                data[entity_type] = {}

            if source_type not in data[entity_type]:
                data[entity_type][source_type] = []

            data[entity_type][source_type].append(row)

        for entity_type in data:
            for source_type in data[entity_type]:
                with open(
                    f"export/entity_sources/{entity_type}__{source_type}.csv", "w"
                ) as out_file:
                    out_writer = csv.DictWriter(
                        out_file,
                        fieldnames=[
                            f"{entity_type}_id",
                            "applicable_entity_properties",
                            f"{source_type}_id",
                            "source_properties",
                        ],
                        lineterminator="\n",
                    )
                    out_writer.writeheader()

                    for row in data[entity_type][source_type]:
                        out_writer.writerow(
                            {
                                f"{entity_type}_id": row["entity_id"],
                                "applicable_entity_properties": row["properties"],
                                f"{source_type}_id": row["source_id"],
                                f"source_properties": row["source_props"],
                            }
                        )

    with open("data/processed/relation_sources.csv") as in_file:
        in_reader = csv.DictReader(in_file)

        data = {}
        for row in in_reader:
            try:
                relation_domain_range = relation_lookup[row["relation_type"]][
                    int(row["relation_id"])
                ]
            except Exception:
                print(
                    f"Relation not found: {row['relation_type']} - {row['relation_id']}"
                )
            source_type = row["source_type"]

            if relation_domain_range not in data:
                data[relation_domain_range] = {}

            if source_type not in data[relation_domain_range]:
                data[relation_domain_range][source_type] = []

            data[relation_domain_range][source_type].append(row)

        for relation_domain_range in data:
            for source_type in data[relation_domain_range]:
                with open(
                    f"export/relation_sources/{relation_domain_range}__{source_type}.csv",
                    "w",
                ) as out_file:
                    out_writer = csv.DictWriter(
                        out_file,
                        fieldnames=[
                            f"relation_id",
                            "applicable_entity_properties",
                            f"{source_type}_id",
                            "source_properties",
                        ],
                        lineterminator="\n",
                    )
                    out_writer.writeheader()

                    for row in data[relation_domain_range][source_type]:
                        out_writer.writerow(
                            {
                                "relation_id": row["relation_id"],
                                "applicable_entity_properties": row["properties"],
                                f"{source_type}_id": row["source_id"],
                                f"source_properties": row["source_props"],
                            }
                        )

    await pool.close()


def main():
    start_time = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(export_data())
    loop.close()
    print(f"Total time: {time.time() - start_time}")


if __name__ == "__main__":
    typer.run(main)
