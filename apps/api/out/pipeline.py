"""
FlowWeaver Generated Preprocessing Script
Pipeline: cuk8wvd3
Generated: 2026-07-20 06:01:51 UTC

This script was compiled from a visual FlowWeaver pipeline.
It is fully standalone and can be run with: python cuk8wvd3.py
"""


from flowweaver.std.io import import_dataset, export_json
from flowweaver.search import search_text
from flowweaver.std.dedup import dedup_exact

def main():
    # --------------------------------------------------------
    # Step 1: Import JSON Dataset
    # --------------------------------------------------------
    raw_dataset = import_dataset(path='data/records.json', root_key='')

    # --------------------------------------------------------
    # Step 2: Search Text
    # --------------------------------------------------------
    dataset = search_text(raw_dataset, column='email', pattern='@acme\\.com$', regex=True)

    # --------------------------------------------------------
    # Step 3: Deduplicate Records
    # --------------------------------------------------------
    deduplicated_dataset = dedup_exact(dataset)

    # --------------------------------------------------------
    # Step 4: Write Json
    # --------------------------------------------------------
    dataset_1 = export_json(deduplicated_dataset, path='out/results.json', pretty=True)


if __name__ == "__main__":
    main()

