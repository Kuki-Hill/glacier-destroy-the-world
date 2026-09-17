# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
Fetch the world's reference-glacier mass balance record once, save the raw
reply to data/, and never fetch again.

    uv run fetch.py

The World Glacier Monitoring Service (WGMS) has tracked a set of "reference"
glaciers around the world every year since the 1950s and published, for each
year, how much mass they have lost or gained on average, added up since the
first year of the record. The US EPA republishes that record as a plain CSV
for its climate change indicators; this is the copy this project reads.
"""

from pathlib import Path

import requests

URL = "https://raw.githubusercontent.com/datasets/glacier-mass-balance/master/data/glaciers.csv"
FILE = "glacier-mass-balance-reference-glaciers.csv"

HERE = Path(__file__).parent
DATA = HERE / "data"


def fetch(url, path):
    """Ask for the file once. If it is already in data/, do nothing."""
    if path.exists():
        print(f"data/{path.name} is already here ({path.stat().st_size // 1024} KB). "
              "Delete it to fetch again.")
        return path
    DATA.mkdir(exist_ok=True)
    print(f"asking {url}")
    reply = requests.get(url, timeout=60, headers={"User-Agent": "SD5913 PolyU student"})
    reply.raise_for_status()
    path.write_bytes(reply.content)      # the raw reply, byte for byte: what arrived is what gets committed
    print(f"saved data/{path.name} ({path.stat().st_size // 1024} KB). Now: git add data")
    return path


if __name__ == "__main__":
    fetch(URL, DATA / FILE)
