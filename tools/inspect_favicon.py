from pathlib import Path
from PIL import Image
p = Path('favicon.ico')
print('exists', p.exists())
if p.exists():
    print('size_bytes', p.stat().st_size)
    try:
        img = Image.open(p)
        print('format', img.format)
        print('mode', img.mode)
        print('size', img.size)
        img.close()
    except Exception as e:
        print('PIL open error:', e)
