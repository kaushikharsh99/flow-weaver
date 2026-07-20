"""
FlowWeaver Generated Preprocessing Script
Pipeline: official_tinystories_pipeline
Generated: Auto-compiled visual DAG script

DO NOT EDIT DIRECTLY — Changes will be overwritten upon compiler re-generation.
"""
from flowweaver.std.io import import_dataset, export_jsonl
from flowweaver.std.text import unicode_normalize, regex_replace

def main():
    raw_dataset = import_dataset(path='/run/media/harsh/STORAGE/Tiny-Stories-Original/TinyStories_all_data')
    normalized_dataset = unicode_normalize(raw_dataset, column='story', form='NFC')
    cleaned_dataset = regex_replace(normalized_dataset, column='story', pattern='\\s+', replacement=' ')
    processed_dataset = export_jsonl(cleaned_dataset, path='out/tinystories_prep.jsonl')
if __name__ == '__main__':
    main()
