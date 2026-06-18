### WRITTEN BY CO-PILOT ###


# **README — Text Processing & Alignment API**

This project provides a Flask‑based API for text processing tasks including:

- **Language detection**
- **Sentence splitting**
- **Sentence alignment**
- **Bilingual mixed‑file alignment** (English ↔ Irish)
- **CSV/TMX generation**
- **Failed‑line extraction**

It is designed to support a React frontend but can be used independently via HTTP requests.

---

## **Endpoints**

### **1. `/langdetect` — GET**

Detects the language of a text string.

**Query parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `text` | string | yes | Text to detect |

**Example**

```
/langdetect?text=Dia%20duit
```

**Response**

```json
{"language": "ga"}
```

---

### **2. `/split` — GET**

Splits text into sentences.

**Query parameters**

| Name | Type | Required |
|------|------|----------|
| `text` | string | yes |

**Example**

```
/split?text=Dia%20duit.%20Conas%20atá%20tú?
```

---

### **3. `/align` — GET**

Aligns two blocks of text (parallel corpora).

**Query parameters**

| Name | Required |
|------|----------|
| `src` | yes |
| `tgt` | yes |

**Example**

```
/align?src=Dia%20duit.&tgt=Hello.
```

---

### **4. `/bilingualalign` — GET**

Processes **a single mixed‑language text** (English + Irish), splits it, detects language, groups sentences, aligns them, and optionally returns failed lines.

**Query parameters**

| Name | Default | Description |
|------|---------|-------------|
| `text` | — | Input text |
| `format` | `csv` | `csv` or `tmx` |
| `output` | `alignment` | `alignment` or `failed` |

**Examples**

Return aligned CSV:

```
/bilingualalign?text=Dia%20duit.%20Hello.&format=csv
```

Return failed lines only:

```
/bilingualalign?text=...&output=failed
```

---

## **5. `/process` — POST**

Main endpoint used by the frontend.  
Accepts uploaded files and performs one of several modes.

### **Modes**

| Mode | Description | Files Required | Output |
|------|-------------|----------------|--------|
| `langdetect` | Detect language | file1 | `.txt` |
| `split` | Sentence split | file1 | `.txt` |
| `align` | Align two files | file1 + file2 | `.csv` or `.tmx` |
| `bilingual_to_aligned` | Mixed‑file bilingual alignment | file1 | `.zip` containing alignment + failed lines |

---

## **Bilingual Processing Logic**

The function `process_bilingual_file(text)`:

1. Splits text into sentences  
2. Detects language for each sentence  
3. Groups into:
   - English lines  
   - Irish lines  
   - Failed lines  
4. Aligns English ↔ Irish using `align_sentences`  
5. Returns:

```python
{
    "alignment": [...],
    "failed_lines": [...]
}
```

The `/process` route packages these into a ZIP:

```
bilingual_alignment.csv or bilingual_alignment.tmx
failed_lines.txt
```

---

## **File Formats**

### **CSV**

Two columns:

```
source,target
Dia duit.,Hello.
...
```

### **TMX**

Standard TMX 1.4 with `<tu>` pairs.

### **Failed Lines**

Plain text file containing one line per failed detection.

---

## **Running the Server**

```
python app.py
```

Server runs at:

```
http://127.0.0.1:5000
```

---

## **Dependencies**

- Flask  
- flask_cors  
- Custom tools:
  - `tools.detector`
  - `tools.splitter`
  - `tools.aligner`
  - `tools.csv_generator`
  - `tools.tmx_generator`
  - `tools.bilingual_to_aligned`

---

## **Project Structure**

```
app.py
tools/
    splitter.py
    detector.py
    aligner.py
    csv_generator.py
    tmx_generator.py
    bilingual_to_aligned.py
requirements.txt
```