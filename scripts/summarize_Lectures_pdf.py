# -------------------------------------------------------------------
# Gemini API configuration
# -------------------------------------------------------------------
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# Define your models in order of preference
MODEL_PREFERENCES = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.5-pro"
]

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

                    # If we hit a Rate Limit, break the retry loop and try the next MODEL
                    if status == 429:
                        print(f"WARNING: Rate limit (429) hit for {model_name}. Failing over to next model...")
                        break 

                    # Retry transient errors
                    if status in (502, 503, 504) and attempt < retries:
                        delay = base_delay * (2 ** (attempt - 1))
                        print(f"WARNING: {model_name} temporary error ({status}). Retrying chunk {part_num} in {delay}s...")
                        time.sleep(delay)
                        continue

                    raise # Re-raise if it's a 400, 403, etc.

                except requests.exceptions.RequestException as e:
                    last_exc = e
                    if attempt < retries:
                        delay = base_delay * (2 ** (attempt - 1))
                        print(f"WARNING: Network error ({e}). Retrying chunk {part_num} in {delay}s...")
                        time.sleep(delay)
                        continue
                    raise
            
            # If the model hit a 429, the loop continues to the next model in MODEL_PREFERENCES.

        # If we exhausted ALL models and still don't have success, it means 
        # we likely hit the daily project cap. We must raise the last exception 
        # to trigger the graceful exit in the main loop.
        if not chunk_success:
            print("CRITICAL: All fallback models exhausted or daily rate limit reached.")
            if last_exc:
                raise last_exc
            else:
                raise Exception("Failed to generate summary with all available models.")

    return "\n\n".join(combined_summary)
