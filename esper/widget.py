from vgrid_jupyter import VGridWidget
from vgrid import VGridSpec
import os

hostname = os.environ.get('HOSTNAME')


def vgrid_widget(**kwargs):
    return VGridWidget(vgrid_spec=VGridSpec(
        video_endpoint='http://{}/system_media'.format(hostname),
        frameserver_endpoint='http://{}:7500/fetch'.format(hostname),
        use_frameserver=True,
        **kwargs).to_json())
