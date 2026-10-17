"""Compose generated pigment onto bare rock; preserve all ancestor pixels elsewhere.
Run once: input wall-v5.png is the imagegen insert, output replaces that same path.
Uses the existing standard-library PNG codec and installed ffmpeg JPEG encoder; no scene rendering.
"""
import hashlib
import json
from pathlib import Path
from finish_wall24 import read_png, write_png
import subprocess


def main():
    wall = Path('artifacts/line-1/wall.png')
    draft = Path('artifacts/line-1/wall-v5.png')
    previous = Path('artifacts/line-1/wall-v4.png').read_bytes()
    w, h, old = read_png(previous)
    dw, dh, pigment = read_png(draft.read_bytes())
    final = old[:]
    # Basket sits below the two branching paths, separate from all old paintings.
    x0, y0, bw, bh = 686, 909, 218, 109
    sx0, sy0, sw, sh = 265, 278, 1010, 510
    for y in range(bh if (dw,dh) != (w,h) else 0):
        for x in range(bw):
            sx = sx0 + int(x * sw / bw)
            sy = sy0 + int(y * sh / bh)
            src = (sy * dw + sx) * 3
            rgb = pigment[src:src+3]
            strength = max(rgb)
            if strength < 40:
                continue
            # Discard black backing, retain only earth/chalk pigment and texture.
            alpha = min(.82, (strength - 40) / 140)
            alpha *= min(1, x/4, y/4, (bw-1-x)/4, (bh-1-y)/4)
            dst = ((y0+y)*w+x0+x)*3
            for c in range(3):
                final[dst+c] = round(old[dst+c]*(1-alpha) + rgb[c]*alpha)
    if (dw,dh) == (w,h):
        final = pigment
    changed = outside = 0
    for p in range(w*h):
        if old[p*3:p*3+3] != final[p*3:p*3+3]:
            changed += 1
            x,y = p%w,p//w
            outside += not (x0 <= x < x0+bw and y0 <= y < y0+bh)
    assert changed > 0 and outside == 0 and (w,h) == (1254,1254)
    digest = write_png(draft,w,h,final)
    assert read_png(draft)[2] == final
    wall.write_bytes(draft.read_bytes())
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(draft),
                    '-vf','scale=512:512','-frames:v','1','-q:v','4',
                    'dist/line-1/25.jpg'], check=True)
    report = {
        'ancestor_sha256': hashlib.sha256(previous).hexdigest(),
        'wall_sha256': digest, 'dimensions': [w,h], 'format': 'PNG', 'mode': 'RGB',
        'wall_paths': ['artifacts/line-1/wall-v5.png','artifacts/line-1/wall.png'],
        'thumbnail': {'path':'dist/line-1/25.jpg','dimensions':[512,512],
                      'format':'JPEG','bytes':Path('dist/line-1/25.jpg').stat().st_size},
        'mark_rectangle':[x0,y0,bw,bh], 'changed_pixels':changed,
        'changed_pixels_outside_rectangle':outside,
        'method':'Installed imagegen pigment insert; in-memory pigment composition onto ancestor.',
        'visual_review': 'Pending inspection of final wall and thumbnail.',
        'unmet_requirements': [
            'The explicit dist/ JPEG requirement conflicts with the blanket prohibition on pictures outside artifacts/. Followed the explicit requested JPEG path.']}
    Path('line-1/IMAGE-25.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
