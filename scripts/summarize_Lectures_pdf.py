import os
import sys
import glob
import hashlib
import tempfile
import subprocess
import atexit
import time
from datetime import datetime

# -------------------------------------------------------------------
# Temporary Environment Setup
# -------------------------------------------------------------------
temp_env_dir = tempfile.mkdtemp()

def cleanup_temp_env():
    import shutil
    shutil.rmtree(temp_env_dir, ignore_errors=True)

atexit.register(cleanup_temp_env)

print("DEBUG: Installing dependencies to a temporary environment...")
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "pypdf", "requests", "--target", temp_env_dir],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

sys.path.insert(0, temp_env_dir)

import requests # type: ignore
from pypdf import PdfReader # type: ignore

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
LECTURES_DIR = "Lectures"
SUMMARY_DIR = os.path.join(LECTURES_DIR, "summaries")
INDEX_FILE = os.path.join(LECTURES_DIR, "index.qmd")

os.makedirs(SUMMARY_DIR, exist_ok=True)

# -------------------------------------------------------------------
# Gemini API configuration
# -------------------------------------------------------------------
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = "gemini-2.5-flash"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# -------------------------------------------------------------------
# Utility: compute a stable hash of PDF contents
# -------------------------------------------------------------------
def pdf_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

# -------------------------------------------------------------------
# Utility: call Gemini API with Retries
# -------------------------------------------------------------------
def summarize_with_gemini(text, retries=5, base_delay=5):
    prompt = f"""
Create a structured Quarto .qmd summary for the following lecture PDF.
Use headings, bullet points, and short explanations.
Focus on clarity and structure.
IMPORTANT: Do NOT wrap your response in markdown code blocks (like ```qmd). Return the raw markdown text directly. Do not include a YAML header, I will generate that automatically.
LATEX WARNING: Ensure all math and symbols are compatible with strict LaTeX rendering. Do NOT use unescaped `#` characters in math mode. For active-low or complementary signals (like clock phases), use standard LaTeX notation such as `\\overline{{\\phi}}` or `\\phi'` instead of `\\phi#`.

PDF content:
{text}
"""

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(GEMINI_URL, json=payload, timeout=60)

            # Retry transient server errors
            if response.status_code in (502, 503, 504):
                raise requests.exceptions.HTTPError(
                    f"{response.status_code} transient error", response=response
                )

            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        except requests.exceptions.HTTPError as e:
            last_exc = e
            status = getattr(e.response, "status_code", None)

            # Keep existing 429 behavior (stop for today, but do not fail)
            if status == 429:
                raise

            # Retry transient errors
            if status in (502, 503, 504) and attempt < retries:
                delay = base_delay * (2 ** (attempt - 1))
                print(f"WARNING: Gemini temporary error ({status}). Retrying in {delay}s (attempt {attempt}/{retries})...")
                time.sleep(delay)
                continue

            raise

        except requests.exceptions.RequestException as e:
            # Network/timeouts -> retry
            last_exc = e
            if attempt < retries:
                delay = base_delay * (2 ** (attempt - 1))
                print(f"WARNING: Network error ({e}). Retrying in {delay}s (attempt {attempt}/{retries})...")
                time.sleep(delay)
                continue
            raise

    raise last_exc

# -------------------------------------------------------------------
# Find PDFs
# -------------------------------------------------------------------
pdf_files = [
    f for f in glob.glob(f"{LECTURES_DIR}/*.pdf") +
              glob.glob(f"{LECTURES_DIR}/*.PDF")
    if "lecture refernce" not in f.lower()
]

print("DEBUG: Scanning folder:", LECTURES_DIR)
print("DEBUG: PDFs found:", pdf_files)

# -------------------------------------------------------------------
# 1. Generate summaries with caching
# -------------------------------------------------------------------
for pdf in pdf_files:
    name = os.path.splitext(os.path.basename(pdf))[0]
    qmd_path = os.path.join(SUMMARY_DIR, f"{name}.qmd")
    hash_path = os.path.join(SUMMARY_DIR, f"{name}.hash")

    # Compute current PDF hash
    current_hash = pdf_hash(pdf)

    # Check if hash file exists and matches
    if os.path.exists(hash_path):
        with open(hash_path, "r") as f:
            old_hash = f.read().strip()
        if old_hash == current_hash:
            print(f"Skipping {pdf} (cached)")
            continue

    # Extract text
    print(f"DEBUG: Processing {pdf}...")
    reader = PdfReader(pdf)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    # Summarize with Gemini (with graceful fail)
    try:
        summary_body = summarize_with_gemini(text)
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        
        # Now catches both Rate Limits and exhausted transient errors
        if status in (429, 502, 503, 504):
            print(f"WARNING: Gemini unavailable (HTTP {status}). Stopping further generation for now.")
            print("The script will exit successfully to allow committing any completed summaries.")
            break
        raise

    # CLEANUP: Remove markdown code block backticks if Gemini added them
    summary_body = summary_body.strip()
    if summary_body.startswith("```"):
        lines = summary_body.split('\n')
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        summary_body = '\n'.join(lines).strip()

    # Create the proper Quarto YAML header
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    yaml_header = f"---\ntitle: \"{name}\"\ndate: \"{timestamp}\"\n---\n\n"
    
    # Combine YAML and body
    summary = yaml_header + summary_body

    # Save summary
    with open(qmd_path, "w", encoding="utf-8") as f:
        f.write(summary)

    # Save hash
    with open(hash_path, "w") as f:
        f.write(current_hash)
        
    print("DEBUG: Summary generated successfully. Pausing for 15 seconds to respect API rate limits...")
    time.sleep(15)

# -------------------------------------------------------------------
# 2. Rebuild Lectures/index.qmd
# -------------------------------------------------------------------
print("DEBUG: Rebuilding index.qmd...")
index_header = """---
title: "Lectures"
---

## Course Lectures

Lecture summaries and source PDFs:
"""

lines = [index_header]

for pdf in sorted(pdf_files):
    name = os.path.splitext(os.path.basename(pdf))[0]
    pdf_rel = os.path.basename(pdf)
    summary_rel = f"summaries/{name}.qmd"
    
    # Only add to index if the summary actually exists
    if os.path.exists(os.path.join(SUMMARY_DIR, f"{name}.qmd")):
        lines.append(f"- [{pdf_rel}]({pdf_rel})  \n  → [Summary]({summary_rel})")

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("DEBUG: Script completed successfully.")
