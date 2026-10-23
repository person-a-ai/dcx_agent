import re
from pathlib import Path

from app.crawl.channels import _DEFAULTS


def test_ts_channel_defaults_match_python():
    source = (Path(__file__).resolve().parents[3] / 'frontend/src/lib/logic/crawlConfig.ts').read_text()
    block = re.search(r'const DEFAULTS: Record<string, \[number, number\]> = \{(.*?)\};', source, re.S)[1]
    ts = {name: (int(c), float(i)) for name, c, i in re.findall(r'(\w+): \[(\d+), ([\d.]+)\]', block)}
    assert ts == {k: (c, float(i)) for k, (c, i) in _DEFAULTS.items()}
