import uuid
from sqlalchemy.orm import Session
from app.models import Template

def seed_templates(db: Session):
    """Seed the database with default AI dataset preprocessing templates if empty."""
    if db.query(Template).count() > 0:
        return

    print("Seeding default FlowWeaver preprocessing templates...")
    
    templates = [
        {
            "id": "tpl_llm_finetuning",
            "name": "LLM Fine-tuning Prep",
            "description": "Clean, format, and serialize dataset instruction-response pairs into JSONL for LLM fine-tuning.",
            "pipeline_data": {
                "nodes": [
                    {
                        "id": "load_1",
                        "type": "pipelineNode",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "typeId": "load_csv",
                            "title": "Load Raw Dataset",
                            "params": {"path": "data/sample.csv", "delimiter": ","}
                        }
                    },
                    {
                        "id": "lowercase_1",
                        "type": "pipelineNode",
                        "position": {"x": 400, "y": 200},
                        "data": {
                            "typeId": "lowercase",
                            "title": "Lowercase Instructions",
                            "params": {"column": "name"}
                        }
                    },
                    {
                        "id": "normalize_1",
                        "type": "pipelineNode",
                        "position": {"x": 700, "y": 200},
                        "data": {
                            "typeId": "unicode_normalize",
                            "title": "Normalize Unicode NFC",
                            "params": {"column": "name", "form": "NFC"}
                        }
                    },
                    {
                        "id": "remove_empty_1",
                        "type": "pipelineNode",
                        "position": {"x": 1000, "y": 200},
                        "data": {
                            "typeId": "remove_empty",
                            "title": "Filter Empty Rows",
                            "params": {"columns": "name,score"}
                        }
                    },
                    {
                        "id": "export_1",
                        "type": "pipelineNode",
                        "position": {"x": 1300, "y": 200},
                        "data": {
                            "typeId": "write_jsonl",
                            "title": "Export Fine-tuning JSONL",
                            "params": {"path": "out/finetuning_prep.jsonl"}
                        }
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "load_1", "target": "lowercase_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e2", "source": "lowercase_1", "target": "normalize_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e3", "source": "normalize_1", "target": "remove_empty_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e4", "source": "remove_empty_1", "target": "export_1", "sourceHandle": "out", "targetHandle": "in_data"}
                ]
            }
        },
        {
            "id": "tpl_rag_prep",
            "name": "RAG Document Prep",
            "description": "Strip HTML formatting, normalize Unicode, and chunk documents using a sliding word window for RAG embeddings.",
            "pipeline_data": {
                "nodes": [
                    {
                        "id": "load_1",
                        "type": "pipelineNode",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "typeId": "load_json",
                            "title": "Load Knowledge Base",
                            "params": {"path": "data/sample.json"}
                        }
                    },
                    {
                        "id": "html_1",
                        "type": "pipelineNode",
                        "position": {"x": 400, "y": 200},
                        "data": {
                            "typeId": "strip_html",
                            "title": "Strip HTML Tags",
                            "params": {"column": "text"}
                        }
                    },
                    {
                        "id": "normalize_1",
                        "type": "pipelineNode",
                        "position": {"x": 700, "y": 200},
                        "data": {
                            "typeId": "unicode_normalize",
                            "title": "Normalize Unicode",
                            "params": {"column": "text", "form": "NFC"}
                        }
                    },
                    {
                        "id": "chunk_1",
                        "type": "pipelineNode",
                        "position": {"x": 1000, "y": 200},
                        "data": {
                            "typeId": "chunk_text",
                            "title": "Sliding Window Chunker",
                            "params": {"column": "text", "chunk_size": 100, "chunk_overlap": 10}
                        }
                    },
                    {
                        "id": "export_1",
                        "type": "pipelineNode",
                        "position": {"x": 1300, "y": 200},
                        "data": {
                            "typeId": "write_jsonl",
                            "title": "Export RAG Chunks",
                            "params": {"path": "out/rag_chunks.jsonl"}
                        }
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "load_1", "target": "html_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e2", "source": "html_1", "target": "normalize_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e3", "source": "normalize_1", "target": "chunk_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e4", "source": "chunk_1", "target": "export_1", "sourceHandle": "out", "targetHandle": "in_data"}
                ]
            }
        },
        {
            "id": "tpl_tinystories",
            "name": "TinyStories Dataset Cleaning",
            "description": "Strip HTML formatting and restrict content to stories within length limits.",
            "pipeline_data": {
                "nodes": [
                    {
                        "id": "load_1",
                        "type": "pipelineNode",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "typeId": "load_jsonl",
                            "title": "Load TinyStories JSONL",
                            "params": {"path": "data/sample.jsonl"}
                        }
                    },
                    {
                        "id": "html_1",
                        "type": "pipelineNode",
                        "position": {"x": 400, "y": 200},
                        "data": {
                            "typeId": "strip_html",
                            "title": "Strip HTML Stories",
                            "params": {"column": "text"}
                        }
                    },
                    {
                        "id": "length_1",
                        "type": "pipelineNode",
                        "position": {"x": 700, "y": 200},
                        "data": {
                            "typeId": "length_filter",
                            "title": "Keep Stories 50-500 words",
                            "params": {"column": "text", "min_len": 50, "max_len": 500}
                        }
                    },
                    {
                        "id": "export_1",
                        "type": "pipelineNode",
                        "position": {"x": 1000, "y": 200},
                        "data": {
                            "typeId": "write_csv",
                            "title": "Export Stories CSV",
                            "params": {"path": "out/stories_clean.csv"}
                        }
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "load_1", "target": "html_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e2", "source": "html_1", "target": "length_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e3", "source": "length_1", "target": "export_1", "sourceHandle": "out", "targetHandle": "in_data"}
                ]
            }
        },
        {
            "id": "tpl_sharegpt",
            "name": "ShareGPT Preprocessing",
            "description": "Align column mappings and replace formatting patterns in multi-turn conversation logs.",
            "pipeline_data": {
                "nodes": [
                    {
                        "id": "load_1",
                        "type": "pipelineNode",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "typeId": "load_json",
                            "title": "Load ShareGPT JSON",
                            "params": {"path": "data/sample.json"}
                        }
                    },
                    {
                        "id": "rename_1",
                        "type": "pipelineNode",
                        "position": {"x": 400, "y": 200},
                        "data": {
                            "typeId": "rename_columns",
                            "title": "Rename to 'conversations'",
                            "params": {"mapping": '{"text": "conversations"}'}
                        }
                    },
                    {
                        "id": "replace_1",
                        "type": "pipelineNode",
                        "position": {"x": 700, "y": 200},
                        "data": {
                            "typeId": "regex_replace",
                            "title": "Clean Spacing",
                            "params": {"column": "conversations", "pattern": "\\s+", "replacement": " "}
                        }
                    },
                    {
                        "id": "export_1",
                        "type": "pipelineNode",
                        "position": {"x": 1000, "y": 200},
                        "data": {
                            "typeId": "write_jsonl",
                            "title": "Export Clean conversations",
                            "params": {"path": "out/sharegpt_clean.jsonl"}
                        }
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "load_1", "target": "rename_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e2", "source": "rename_1", "target": "replace_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e3", "source": "replace_1", "target": "export_1", "sourceHandle": "out", "targetHandle": "in_data"}
                ]
            }
        },
        {
            "id": "tpl_ocr_postprocess",
            "name": "OCR Post-Processing",
            "description": "Fix punctuation artifacts and clean spelling issues from scanned OCR texts.",
            "pipeline_data": {
                "nodes": [
                    {
                        "id": "load_1",
                        "type": "pipelineNode",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "typeId": "load_csv",
                            "title": "Load Raw OCR CSV",
                            "params": {"path": "data/sample.csv"}
                        }
                    },
                    {
                        "id": "ocr_fix_1",
                        "type": "pipelineNode",
                        "position": {"x": 400, "y": 200},
                        "data": {
                            "typeId": "regex_replace",
                            "title": "Fix Spacing Artifacts",
                            "params": {"column": "name", "pattern": "\\s*([.,?!])\\s*", "replacement": "\\1 "}
                        }
                    },
                    {
                        "id": "length_1",
                        "type": "pipelineNode",
                        "position": {"x": 700, "y": 200},
                        "data": {
                            "typeId": "length_filter",
                            "title": "Filter OCR noise",
                            "params": {"column": "name", "min_len": 3}
                        }
                    },
                    {
                        "id": "export_1",
                        "type": "pipelineNode",
                        "position": {"x": 1000, "y": 200},
                        "data": {
                            "typeId": "write_csv",
                            "title": "Export Clean OCR",
                            "params": {"path": "out/ocr_clean.csv"}
                        }
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "load_1", "target": "ocr_fix_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e2", "source": "ocr_fix_1", "target": "length_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e3", "source": "length_1", "target": "export_1", "sourceHandle": "out", "targetHandle": "in_data"}
                ]
            }
        },
        {
            "id": "tpl_common_crawl",
            "name": "Common Crawl Processing",
            "description": "Strip HTML, extract English text, remove duplicates, and store as binary Parquet format.",
            "pipeline_data": {
                "nodes": [
                    {
                        "id": "load_1",
                        "type": "pipelineNode",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "typeId": "load_jsonl",
                            "title": "Load Web Crawl JSONL",
                            "params": {"path": "data/sample.jsonl"}
                        }
                    },
                    {
                        "id": "html_1",
                        "type": "pipelineNode",
                        "position": {"x": 400, "y": 200},
                        "data": {
                            "typeId": "strip_html",
                            "title": "Strip HTML markup",
                            "params": {"column": "text"}
                        }
                    },
                    {
                        "id": "lang_1",
                        "type": "pipelineNode",
                        "position": {"x": 700, "y": 200},
                        "data": {
                            "typeId": "language_filter",
                            "title": "Filter English Content",
                            "params": {"column": "text", "target_lang": "en"}
                        }
                    },
                    {
                        "id": "dedup_1",
                        "type": "pipelineNode",
                        "position": {"x": 1000, "y": 200},
                        "data": {
                            "typeId": "dedup_exact",
                            "title": "Remove Exact Duplicates",
                            "params": {"columns": "text"}
                        }
                    },
                    {
                        "id": "export_1",
                        "type": "pipelineNode",
                        "position": {"x": 1300, "y": 200},
                        "data": {
                            "typeId": "write_parquet",
                            "title": "Export Parquet Output",
                            "params": {"path": "out/crawl_preprocessed.parquet"}
                        }
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "load_1", "target": "html_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e2", "source": "html_1", "target": "lang_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e3", "source": "lang_1", "target": "dedup_1", "sourceHandle": "out", "targetHandle": "in_data"},
                    {"id": "e4", "source": "dedup_1", "target": "export_1", "sourceHandle": "out", "targetHandle": "in_data"}
                ]
            }
        }
    ]
    
    for tpl in templates:
        t = Template(
            id=tpl["id"],
            name=tpl["name"],
            description=tpl["description"],
            pipeline_data=tpl["pipeline_data"]
        )
        db.add(t)
        
    db.commit()
    print("✔ 6 default preprocessing templates seeded successfully.")
