from esper.models import Video
from esper.lib.queries import register_query

@register_query("All videos")
def all_videos():
    return Video.objects.all()
