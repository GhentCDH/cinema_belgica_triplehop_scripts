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
) -> typing.Dict[str,typing.Dict]:
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
        config = json.loads(record['config'])
        if not 'data' in config:
            continue
        if not 'fields' in config['data']:
            continue
        result = {}
        for field, field_data in config['data']['fields'].items():
            result[field] = field_data['system_name']
        results[record['system_name']] = {
            'id': str(record['id']),
            'props': result,
        }

    return results

async def get_entities(
    pool: asyncpg.pool.Pool,
    project_name: str,
    entity_type_id: str,
    props_config: typing.Dict[str,str],
)-> typing.List[typing.Dict]:
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
        raw_data = json.loads(record['n'][:-8])['properties']
        result = {
            'id': raw_data['id'],
        }
        for prop_id, prop_name in props_config.items():
            if prop_name == 'original_id':
                continue
            p_id = f'p_{db_base.dtu(prop_id)}'
            if p_id not in raw_data:
                continue
            result[prop_name] = raw_data[p_id]
        results.append(result)
    return results


async def export_data():
    pool = await asyncpg.create_pool(**config.DATABASE)

    entities_props = await get_entities_props(
        pool=pool,
        project_name='cinema_belgica',
    )
    for entity_type_name, entity_config in entities_props.items():
        # Prepend id, add all props except for original_id
        columns = ['id', *[v for v in entity_config['props'].values() if v != 'original_id']]
        with open (f'export/entities/{entity_type_name}.csv', 'w') as out_file:
            out_writer = csv.DictWriter(
                out_file,
                fieldnames=columns
            )
            out_writer.writeheader()

            data = await get_entities(
                pool=pool,
                project_name='cinema_belgica',
                entity_type_id=entity_config['id'],
                props_config=entity_config['props'],
            )
            for row in data:
                out_writer.writerow(row)

    await pool.close()

def main():
    start_time = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(export_data())
    loop.close()
    print(f"Total time: {time.time() - start_time}")


if __name__ == "__main__":
    typer.run(main)
