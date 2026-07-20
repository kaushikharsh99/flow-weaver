"""
FlowWeaver Generated Preprocessing Script
Pipeline: 72p6ysmj
Generated: 2026-07-20 06:08:57 UTC

This script was compiled from a visual FlowWeaver pipeline.
It is fully standalone and can be run with: python 72p6ysmj.py
"""


from flowweaver.std.io import import_dataset, export_csv
from flowweaver.std.tabular import sample_rows
from flowweaver.std.dedup import dedup_exact

def main():
    # --------------------------------------------------------
    # Step 1: Import CSV Dataset
    # --------------------------------------------------------
    raw_dataset = import_dataset(path='data/users.csv', delimiter=',')

    # --------------------------------------------------------
    # Step 2: Sample Random Subset of Rows
    # --------------------------------------------------------
    sampled_dataset = sample_rows(raw_dataset, n=100, seed=42)

    # --------------------------------------------------------
    # Step 3: Deduplicate Records
    # --------------------------------------------------------
    deduplicated_dataset = dedup_exact(sampled_dataset)

    # --------------------------------------------------------
    # Step 4: Export to CSV
    # --------------------------------------------------------
    processed_dataset = export_csv(deduplicated_dataset, path='out/results.csv')


if __name__ == "__main__":
    main()

