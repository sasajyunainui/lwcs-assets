# 头像 / 立绘原图（dldl_work/立绘/生成后）转 WebP 到 characters/：头像 320px、立绘竖版 683x1024 / 横版 1024x683，质量 82；
# 转完按 aliases.json 改名、排除、加别名，再重建 characters/manifest.json。
# 用法：python convert-portraits.py            全量转换
#       python convert-portraits.py --overrides-only   只套 aliases.json 并重建清单
import json, os, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

SRC = r'D:/silltyavern/tavern_helper_template-main/tavern_helper_template-main/dldl_work/立绘/生成后'
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'characters')
BOOK = {'斗一': 'dl1', '斗二': 'dl2', '斗三': 'dl3', '斗四': 'dl4'}
OVERRIDES = json.load(open(os.path.join(ROOT, 'aliases.json'), encoding='utf-8'))


def convert(name):
    stem = name[:-len('.png')]
    kind = 'avatar' if stem.endswith('-avatar') else 'standing'
    im = Image.open(os.path.join(SRC, name)).convert('RGBA')
    if kind == 'avatar':
        box = (320, 320)
    else:
        box = (1024, 683) if im.width > im.height else (683, 1024)
    im.thumbnail(box, Image.LANCZOS)
    im.save(os.path.join(OUT, stem + '.webp'), 'WEBP', quality=82, method=4)
    return name


# aliases.json：rename 把「时代-旧名」的两张图改成新名，exclude 的图不进图集，aliases 写进清单
def apply_overrides():
    for old, new in OVERRIDES.get('rename', {}).items():
        for kind in ('avatar', 'standing'):
            src = os.path.join(OUT, f'{old}-{kind}.webp')
            if os.path.exists(src):
                os.replace(src, os.path.join(OUT, f'{new}-{kind}.webp'))
    for name in OVERRIDES.get('exclude', []):
        for kind in ('avatar', 'standing'):
            path = os.path.join(OUT, f'{name}-{kind}.webp')
            if os.path.exists(path):
                os.remove(path)


def build_manifest():
    chars = {}
    for f in sorted(os.listdir(OUT)):
        if not f.endswith('.webp'):
            continue
        era, rest = f.split('-', 1)
        cname, kind = rest[:-len('.webp')].rsplit('-', 1)
        entry = chars.setdefault((era, cname), {'id': f'{BOOK[era]}:{cname}', 'name': cname, 'book': BOOK[era], 'aliases': OVERRIDES.get('aliases', {}).get(f'{era}-{cname}', [])})
        entry[kind] = f
    with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'version': 3, 'characters': list(chars.values())}, fh, ensure_ascii=False, indent=1)
    return chars


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(f for f in os.listdir(SRC) if f.endswith('-avatar.png') or f.endswith('-standing.png'))
    done = 0
    with ProcessPoolExecutor(max_workers=6) as pool:
        for _ in pool.map(convert, files, chunksize=8):
            done += 1
            if done % 200 == 0:
                print(f'{done}/{len(files)}', flush=True)
    apply_overrides()
    chars = build_manifest()
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    missing = [c['id'] for c in chars.values() if not c.get('avatar') or not c.get('standing')]
    print(f'done {len(files)} files, {len(chars)} characters, {total / 1048576:.1f} MB, missing pair {len(missing)}')


if __name__ == '__main__':
    if '--overrides-only' in sys.argv:
        apply_overrides()
        print(f'overrides applied, {len(build_manifest())} characters')
    else:
        main()
