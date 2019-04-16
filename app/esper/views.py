from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from timeit import default_timer as now
import django.db.models as models
from concurrent.futures import ThreadPoolExecutor
from django.views.decorators.csrf import csrf_exempt
import sys
import json
import os
import tempfile
import subprocess as sp
import shlex
import math
import pysrt
import requests
import enum
from storehouse import StorageConfig, StorageBackend
import traceback
from pprint import pprint
import django.apps

ESPER_ENV = os.environ.get('ESPER_ENV')
BUCKET = os.environ.get('BUCKET')
DATA_PATH = os.environ.get('DATA_PATH')

if ESPER_ENV == 'google':
    storage_config = StorageConfig.make_gcs_config(BUCKET)
else:
    storage_config = StorageConfig.make_posix_config()
storage = StorageBackend.make_from_config(storage_config)

VTT_FROM_CAPTION_INDEX = True


# Renders home page
def index(request):
    import app.queries
    from esper.lib.queries import QUERIES

    def get_fields(cls):
        fields = cls._meta.get_fields()
        return [f.name for f in fields if isinstance(f, models.Field)]

    schema = []
    for m in django.apps.apps.get_models():
        schema.append([m.__name__, get_fields(m)])

    globls = {
        'bucket': BUCKET,
        'schema': schema,
        'queries': QUERIES,
    }

    return render(request, 'index.html', {'globals': json.dumps(globls)})


# Run search routine
def search(request):
    params = json.loads(request.body.decode('utf-8'))

    def make_error(err):
        return JsonResponse({'error': err})

    try:
        ############### vvv DANGER -- REMOTE CODE EXECUTION vvv ###############
        _globals = {}
        _locals = {}
        for k in globals():
            _globals[k] = globals()[k]
        for k in locals():
            _locals[k] = locals()[k]
        exec((params['code']), _globals, _locals)
        result = _locals['FN']()
        ############### ^^^ DANGER -- REMOTE CODE EXECUTION ^^^ ###############

        if not isinstance(result, dict):
            return make_error(
                'Result must be a dict {{result, count, type}}, received type {}'.format(
                    type(result)))

        if not isinstance(result['result'], list):
            return make_error('Result must be a frame list')

        return JsonResponse({'success': result_with_metadata(result)})

    except Exception:
        return make_error(traceback.format_exc())


# Get distinct values in schema
def schema(request):
    params = json.loads(request.body.decode('utf-8'))

    cls = next(m for m in django.apps.apps.get_models() if m.__name__ == params['cls_name'])
    result = [
        r[params['field']]
        for r in cls.objects.values(params['field']).distinct().order_by(params['field'])[:100]
    ]
    try:
        json.dumps(result)
    except TypeError as e:
        return JsonResponse({'error': str(e)})

    return JsonResponse({'result': result})


# Convert captions in SRT format to WebVTT (for displaying in web UI)
def srt_to_vtt(s, shift):
    subs = pysrt.from_string(s)
    subs.shift(shift)  # Seems like TV news captions are delayed by a few seconds

    entry_fmt = '{position}\n{start} --> {end}\n{text}'

    def fmt_time(t):
        return '{:02d}:{:02d}:{:02d}.{:03d}'.format(t.hours, t.minutes, t.seconds, t.milliseconds)

    entries = [
        entry_fmt.format(
            position=i, start=fmt_time(sub.start), end=fmt_time(sub.end), text=sub.text)
        for i, sub in enumerate(subs)
    ]

    return '\n\n'.join(['WEBVTT'] + entries)


# Get subtitles for video
def subtitles(request):
    video_id = request.GET.get('video')
    use_json = request.GET.get('json')

    if use_json:
        import esper.captions as captions
        return JsonResponse({'captions': captions.get_json(int(video_id))})
    else:
        if VTT_FROM_CAPTION_INDEX:
            import esper.captions as captions
            vtt = captions.get_vtt(int(video_id))
        else:
            video = Video.objects.get(id=video_id)
            srt_dir = '/app/data/subs/orig'
            for f in os.listdir(srt_dir):
                if video.item_name() in f:
                    sub_path = os.path.join(srt_dir, f)
                    break
            else:
                return HttpResponseNotFound()

            s = open(sub_path, 'rb').read().decode('utf-8')
            vtt = srt_to_vtt(s, 0)

        return HttpResponse(vtt, content_type="text/vtt")
