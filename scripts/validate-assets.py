"""Reject broken/error SVGs before publishing profile cards."""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
for name in ('banner.svg', 'stats.svg', 'languages.svg'):
    raw = (root / 'assets' / name).read_text(encoding='utf-8')
    tree = ET.fromstring(raw)
    assert tree.tag == '{http://www.w3.org/2000/svg}svg', f'{name}: not an SVG'
    assert 'Something went wrong' not in raw, f'{name}: service error card'
    assert not any(e.tag.rsplit('}', 1)[-1] == 'script' for e in tree.iter())
    print(f'OK: {name}')
