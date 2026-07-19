# Tutorial: LLM Fine-Tuning Prep

This tutorial guides you through using FlowWeaver to load a raw CSV dataset of instruction-response pairs, clean spelling artifacts, normalize text representations, and export a clean `.jsonl` document suitable for Llama 3 fine-tuning.

---

## What We Will Build
We will build a horizontal pipeline connecting:
1. `Load CSV` — Reads the raw dataset from disk.
2. `Strip HTML` — Removes any scraped HTML tags.
3. `Lowercase Text` — Standardizes instruction case models.
4. `Remove Empty Rows` — Drops incomplete records.
5. `Write JSON Lines` — Serializes clean output.

---

## Step 1: Load Raw Dataset
1. Open the visual builder.
2. Search for **Load CSV** in the Sidebar palette and drag it onto the canvas.
3. Select the node and configure the **File path** parameter in the right-hand Inspector:
   - `File path`: `data/sample.csv`
4. Confirm **Delimiter** is set to `Comma`.

---

## Step 2: Strip HTML Noise
1. Drag the **Strip HTML** node onto the canvas.
2. Connect the `out` port of `Load CSV` to the `in_data` port of `Strip HTML`.
3. In the Inspector, specify the column containing the instruction text:
   - `Target Column`: `name`

---

## Step 3: Standardize Text Case
1. Drag the **Lowercase Text** node onto the canvas.
2. Connect `Strip HTML (out)` → `Lowercase Text (in_data)`.
3. Select `Lowercase Text` and verify the column parameter matches:
   - `Target Column`: `name`

---

## Step 4: Drop Incomplete Records
1. Drag the **Remove Empty Rows** node onto the canvas.
2. Connect `Lowercase Text (out)` → `Remove Empty Rows (in_data)`.
3. In the Inspector, specify which columns are required to be non-empty:
   - `Target Columns`: `name,score`

---

## Step 5: Export to JSON Lines
1. Drag the **Write JSON Lines** node onto the canvas.
2. Connect `Remove Empty Rows (out)` → `Write JSON Lines (in_data)`.
3. Configure the export destination path:
   - `Output path`: `out/llama3_finetuning.jsonl`

---

## Step 6: Execute & Verify
1. Click the **Run** button in the top toolbar.
2. The canvas nodes will turn green sequentially as they process records.
3. Select the final `Write JSON Lines` node. Look at the Inspector's **Edge Data Preview** tab:
   - Verify the schema shows text/numbers clearly.
   - Inspect the processed rows snippet.
4. Open a shell terminal and verify the output document exists and is formatted correctly:
   ```bash
   head -n 2 out/llama3_finetuning.jsonl
   ```
   Output:
   ```json
   {"id": "1", "name": "alpha", "score": "92.5"}
   {"id": "2", "name": "beta", "score": "78.1"}
   ```
Congratulations! You have preprocessed your first instruction tuning dataset using FlowWeaver.
