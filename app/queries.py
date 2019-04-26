from app.models import Video
from esperlib.queries import register_query


@register_query("All videos")
def all_videos():
    from app.models import Video
    from vgrid import VideoVBlocksBuilder, VideoTrackBuilder, VideoMetadata
    from rekall import IntervalSet, Interval, Bounds3D, IntervalSetMapping

    videos = Video.objects.all()

    json = VideoVBlocksBuilder() \
        .add_track(VideoTrackBuilder(
            'videos', IntervalSetMapping({v.id: IntervalSet([Interval(Bounds3D(0, v.duration()))])
                                          for v in videos}))) \
        .add_video_metadata(
            '/system_media', [VideoMetadata(**{k: getattr(v, k)
                                               for k in ['id', 'path', 'num_frames', 'fps', 'width', 'height']})
                              for v in videos]) \
        .build()

    return json
