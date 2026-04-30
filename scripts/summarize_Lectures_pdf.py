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
# Gemini API configuration & Fallbacks
# -------------------------------------------------------------------
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# Define your models in order of preference. 
# If the first hits a Rate Limit (429), it will seamlessly failover to the next.
MODEL_PREFERENCES = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.5-pro"
]

# -------------------------------------------------------------------
# Utility: compute a stable hash of PDF contents
# -------------------------------------------------------------------
def pdf_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

# -------------------------------------------------------------------
# Utility: Minimal Viable Test (MVT)
# -------------------------------------------------------------------
def run_api_mvt():
    """Pings the primary Gemini API model to check general server health."""
    print(f"DEBUG: Running API MVT (Health Check) on {MODEL_PREFERENCES[0]}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_PREFERENCES[0]}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": "MVT Ping."}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        print("DEBUG: API MVT Passed. Servers are reachable.")
        return True
    except requests.exceptions.RequestException as e:
        status = getattr(e.response, "status_code", None)
        print(f"WARNING: API MVT Failed. HTTP {status}. Server might be down or unreachable.")
        return False

# -------------------------------------------------------------------
# Utility: Chunk text to avoid payload limits
# -------------------------------------------------------------------
def chunk_text(text, max_chars=60000):
    """Splits text into chunks, preferring to break at paragraphs or newlines."""
    chunks = []
    while len(text) > max_chars:
        # Try to split at the last double newline within the limit
        split_idx = text.rfind('\n\n', 0, max_chars)
        
        # Fallback to single newline
        if split_idx == -1:
            split_idx = text.rfind('\n', 0, max_chars)
            
        # Hard fallback if no newlines exist
        if split_idx == -1:
            split_idx = max_chars
            
        chunks.append(text[:split_idx].strip())
        text = text[split_idx:].strip()
        
    if text:
        chunks.append(text)
    return chunks

# -------------------------------------------------------------------
# Utility: call Gemini API with Retries, Chunking, and Fallbacks
# -------------------------------------------------------------------
def summarize_with_gemini(text, retries=5, base_delay=5):
    chunks = chunk_text(text)
    total_chunks = len(chunks)
    combined_summary = []

    for i, chunk in enumerate(chunks):
        part_num = i + 1
        
        if total_chunks > 1:
            print(f"DEBUG: Processing chunk {part_num} of {total_chunks}...")
            context_note = f"This is PART {part_num} OF {total_chunks} of a larger lecture PDF. Please summarize this specific section. Ensure the output flows seamlessly so it can be concatenated with the other parts."
        else:
            context_note = "Please summarize the following lecture PDF."

        prompt = f"""
Create a structured Quarto .qmd summary. {context_note}
Use headings, bullet points, and short explanations.
Focus on clarity and structure.
IMPORTANT: Do NOT wrap your response in markdown code blocks (like ```qmd). Return the raw markdown text directly. Do not include a YAML header, I will generate that automatically.
LATEX WARNING: Ensure all math and symbols are compatible with strict LaTeX rendering. Do NOT use unescaped `#` characters in math mode. For active-low or complementary signals (like clock phases), use standard LaTeX notation such as `\\overline{{\\phi}}` or `\\phi'` instead of `\\phi#`.
IMAGE WARNING: Do NOT include any markdown image links (e.g., `![alt text](image.png)`). The Quarto compilation will fail because the local image files do not exist. If a visual diagram or graph from the lecture is crucial, describe its behavior in text or represent its mathematical relationship via LaTeX.

PDF content:
{chunk}
"""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        chunk_success = False

        # Loop through the available models
        for model_name in MODEL_PREFERENCES:
            if chunk_success:
                break # Move to the next chunk if we succeeded

            gemini_url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){model_name}:generateContent?key={GEMINI_API_KEY}"
            print(f"DEBUG: Attempting with model: {model_name}")

            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    response = requests.post(gemini_url, json=payload, timeout=60)

                    # Retry transient server errors
                    if response.status_code in (502, 503, 504):
                        raise requests.exceptions.HTTPError(
                            f"{response.status_code} transient error", response=response
                        )

                    response.raise_for_status()
                    data = response.json()
                    
                    chunk_summary = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if chunk_summary.startswith("```"):
                        lines = chunk_summary.split('\n')
                        if lines[0].startswith("```"): lines = lines[1:]
                        if lines[-1].startswith("```"): lines = lines[:-1]
                        chunk_summary = '\n'.join(lines).strip()
                    
                    combined_summary.append(chunk_summary)
                    chunk_success = True
                    
                    if total_chunks > 1 and part_num < total_chunks:
                        time.sleep(2)
                        
                    break # Break retry loop on success

                except requests.exceptions.HTTPError as e:
                    last_exc = e
                    status = getattr(e.response, "status_code", None)

                    # If we hit a Rate Limit, break the retry loop and failover to the next MODEL
                    if status == 429:
                        print(f"WARNING: Rate limit (429) hit for {model_name}. Failing over to next model...")
                        break 

                    # Retry transient errors
                    if status in (502, 503, 504) and attempt < retries:
                        delay = base_delay * (2 ** (attempt - 1))
                        print(f"WARNING: {model_name} temporary error ({status}). Retrying chunk {part_num} in {delay}s (attempt {attempt}/{retries})...")
                        time.sleep(delay)
                        continue

                    raise # Re-raise if it's a 400, 403, etc.

                except requests.exceptions.RequestException as e:
                    last_exc = e
                    if attempt < retries:
                        delay = base_delay * (2 ** (attempt - 1))
                        print(f"WARNING: Network error ({e}). Retrying chunk {part_num} in {delay}s (attempt {attempt}/{retries})...")
                        time.sleep(delay)
                        continue
                    raise
            
        # If we exhausted ALL models and still don't have success, it means 
        # we likely hit the daily project cap. Throw back to main loop for graceful exit.
        if not chunk_success:
            print("CRITICAL: All fallback models exhausted or daily rate limit reached.")
            if last_exc:
                raise last_exc
            else:
                raise Exception("Failed to generate summary with all available models.")

    return "\n\n".join(combined_summary)

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

# Run MVT before starting the heavy processing
if not run_api_mvt():
    print("WARNING: Skipping PDF processing due to failed API Health Check.")
    print("The script will exit successfully to allow deployment of previously completed summaries.")
    sys.exit(0)

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
    except Exception as e:
        # Check if the exception was an HTTP error passed up from the fallback loop
        if isinstance(e, requests.exceptions.HTTPError):
            status = getattr(e.response, "status_code", None)
            if status in (429, 502, 503, 504):
                print(f"WARNING: API unavailable (HTTP {status}) across all models. Stopping generation.")
                print("The script will exit successfully to allow committing any completed summaries.")
                break
            raise
        else:
            # If it's the custom "All models exhausted" exception or a network timeout
            print(f"WARNING: API pipeline failed: {e}. Stopping generation.")
            print("The script will exit successfully to allow committing any completed summaries.")
            break

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
