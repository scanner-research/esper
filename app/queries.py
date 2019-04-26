from app.models import Video
from esperlib.queries import register_query


@register_query("All videos")
def all_videos():
    return Video.objects.all()
