"""
FlowWeaver Generated Preprocessing Script
Pipeline: sample_cli_pipeline
Generated: Auto-compiled visual DAG script

DO NOT EDIT DIRECTLY — Changes will be overwritten upon compiler re-generation.
"""
from flowweaver.std.io import import_dataset, export_jsonl
from flowweaver.std.text import lowercase

def main():
    dataset = import_dataset(path='data/sample.csv', delimiter=',')
    dataset_1 = lowercase(dataset, column='instruction')
    dataset_2 = export_jsonl(dataset_1, path='out/clean.jsonl')
if __name__ == '__main__':
    main()
