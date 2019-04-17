import subprocess as sp
from iterextras import par_for
import traceback
from django.apps import apps
from pathlib import Path
import os


def export_to_csv(model, output_path=None):
    model_name = model._meta.db_table
    if output_path is None:
        Path('/app/data/postgres').mkdir(parents=True, exist_ok=True)
        output_path = '/app/data/postgres/{}.csv'.format(model_name)

    script = """
    bash -c 'rm -f {output} && (echo "\copy (SELECT * FROM {table}) TO '{output}' WITH CSV HEADER;" | psql -h db esper {user})'
    """.format(table=model_name,
               output=output_path,
               user=os.environ.get('POSTGRES_USER'))

    try:
        sp.check_call(script, shell=True)
    except Exception:
        print(model_name)
        traceback.print_exc()

    return output_path


def export_all_to_csv():
    models = apps.get_models(include_auto_created=True)
    return models, par_for(export_to_csv, models, workers=8)
