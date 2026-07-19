# Preprocessing Examples

FlowWeaver ships with 6 default preprocessing templates designed to address common AI dataset pre-run cleaning challenges. You can import these directly on the visual canvas.

---

## 1. LLM Fine-Tuning Prep
Prepares custom raw instructions and scores datasets for instruction-tuning runs:
- **Pipeline Layout**: `Load CSV` → `Lowercase Text` → `Unicode Normalize` → `Remove Empty Rows` → `Write JSON Lines`
- **Output**: Generates a `.jsonl` document (one instruction/output map per line) compatible with Llama or Mistral fine-tuning pipelines.

---

## 2. RAG Document Prep
Prepares multi-source documentation for document vector databases (e.g. Pinecone, Chroma):
- **Pipeline Layout**: `Load JSON` → `Strip HTML` → `Unicode Normalize` → `Text Chunking` → `Write JSON Lines`
- **Goal**: Cleans HTML noise and splits files into overlaps of words (sliding windows) to ensure sentence embedding context boundaries are preserved.

---

## 3. TinyStories Dataset Cleaning
Filters and prunes short narrative datasets for training small-scale language models:
- **Pipeline Layout**: `Load JSONL` → `Strip HTML` → `Length Filter` → `Write CSV`
- **Goal**: Crops formatting tags and filters stories that fall outside target character length bounds (e.g. keeping only 50-500 words).

---

## 4. ShareGPT Preprocessing
Formats conversational chat logs for chat-model fine-tuning:
- **Pipeline Layout**: `Load JSON` → `Rename Columns` → `Regex Replace` → `Write JSONL`
- **Goal**: Aligns inconsistent column headers into a unified chat conversations format and cleans whitespace formatting.

---

## 5. OCR Post-Processing
Cleans artifacts from optical character recognition (OCR) document scans:
- **Pipeline Layout**: `Load CSV` → `Regex Replace` → `Length Filter` → `Write CSV`
- **Goal**: Corrects punctuation spacing errors (e.g. `\s*([.,?!])\s*`) and filters out short OCR scanning noise.

---

## 6. Common Crawl Processing
A heavy pipeline to preprocess web-scale crawling datasets:
- **Pipeline Layout**: `Load JSONL` → `Strip HTML` → `Language Filter` → `Dedup Exact` → `Write Parquet`
- **Goal**: Strips HTML webpage wrappers, filters out non-English content, deduplicates identical pages, and outputs compact binary Parquet files.
