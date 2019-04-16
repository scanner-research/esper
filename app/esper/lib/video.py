import requests
import cv2
from iterextras import par_for
import tempfile
import subprocess as sp


def crop(img, bbox):
    [h, w] = img.shape[:2]
    return img[int(bbox.bbox_y1 * h):int(bbox.bbox_y2 * h),
               int(bbox.bbox_x1 * w):int(bbox.bbox_x2 * w)]


def resize(img, w, h):
    th = int(img.shape[0] * (w / float(img.shape[1]))) if h is None else int(h)
    tw = int(img.shape[1] * (h / float(img.shape[0]))) if w is None else int(w)
    return cv2.resize(img, (tw, th))


def load_frame(video, frame, bboxes):
    while True:
        try:
            r = requests.get('http://frameserver:7500/fetch',
                             params={
                                 'path': video.path,
                                 'frame': frame,
                             })
            break
        except requests.ConnectionError:
            pass
    img = cv2.imdecode(np.fromstring(r.content, dtype=np.uint8),
                       cv2.IMREAD_UNCHANGED)
    if img is None:
        raise Exception("Bad frame {} for {}".format(frame, video.path))
    for bbox in bboxes:
        img = cv2.rectangle(img, (int(bbox['bbox_x1'] * img.shape[1]),
                                  int(bbox['bbox_y1'] * img.shape[0])),
                            (int(bbox['bbox_x2'] * img.shape[1]),
                             int(bbox['bbox_y2'] * img.shape[0])), (0, 0, 255),
                            8)

    return img


def make_montage(video,
                 frames,
                 output_path=None,
                 bboxes=None,
                 width=1600,
                 num_cols=8,
                 workers=16,
                 target_height=None,
                 progress=False):
    target_width = int(width / num_cols)

    bboxes = bboxes or [[] for _ in range(len(frames))]
    videos = video if isinstance(
        video, list) else [video for _ in range(len(frames))]
    imgs = par_for(lambda t: resize(load_frame(*t), target_width, target_height
                                    ),
                   list(zip(videos, frames, bboxes)),
                   progress=progress,
                   workers=workers)
    target_height = int(imgs[0].shape[0])
    num_rows = int(math.ceil(float(len(imgs)) / num_cols))

    montage = np.zeros((num_rows * target_height, width, 3), dtype=np.uint8)
    for row in range(num_rows):
        for col in range(num_cols):
            i = row * num_cols + col
            if i >= len(imgs):
                break
            img = imgs[i]
            montage[row * target_height:(row + 1) * target_height, col *
                    target_width:(col + 1) * target_width, :] = img
        else:
            continue
        break

    if output_path is not None:
        cv2.imwrite(output_path, montage)
    else:
        return montage


def shot_montage(video, **kwargs):
    from query.models import Frame
    return make_montage(video, [
        f['number']
        for f in Frame.objects.filter(video=video, shot_boundary=True).
        order_by('number').values('number')
    ], **kwargs)


def _get_frame(args):
    (videos, fps, start, i, kwargs) = args
    return make_montage(
        videos, [int(math.ceil(v.fps)) / fps * i + start for v in videos],
        **kwargs)


def make_montage_video(videos, start, end, output_path, **kwargs):
    def gcd(a, b):
        return gcd(b, a % b) if b else a

    fps = reduce(gcd, [int(math.ceil(v.fps)) for v in videos])

    first = _get_frame((videos, fps, start, 0, kwargs))
    vid = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'XVID'), fps,
                          (first.shape[1], first.shape[0]))

    frames = par_for(_get_frame, [(videos, fps, start, i, kwargs)
                                  for i in range(end - start)],
                     workers=8,
                     process=True)
    for frame in tqdm(frames):
        vid.write(frame)

    vid.release()


def concat_videos(paths, output_path=None):
    if output_path is None:
        output_path = tempfile.NamedTemporaryFile(suffix='.mp4',
                                                  delete=False).name

    transform = ';'.join([
        '[{i}:v]scale=640:480:force_original_aspect_ratio=decrease,pad=640:480:(ow-iw)/2:(oh-ih)/2[v{i}]'
        .format(i=i) for i in range(len(paths))
    ])
    filter = ''.join(
        ['[v{i}][{i}:a:0]'.format(i=i) for i in range(len(paths))])
    inputs = ' '.join(['-i {}'.format(p) for p in paths])

    cmd = '''
    ffmpeg -y {inputs} \
    -filter_complex "{transform}; {filter}concat=n={n}:v=1:a=1[outv][outa]" \
    -map "[outv]" -map "[outa]" {output}
    '''.format(transform=transform,
               inputs=inputs,
               filter=filter,
               n=len(paths),
               output=output_path)
    sp.check_call(cmd, shell=True)

    return output_path
