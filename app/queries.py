from server.models import Video
from esper.queries import register_query


@register_query("All videos")
def all_videos():
    return Video.objects.all()
