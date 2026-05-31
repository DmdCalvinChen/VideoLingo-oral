import sys, os
import pandas as pd
import json
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt
from core.config_utils import load_key

PUNCTUATED_TEXT_FILE = "output/log/punctuated_text.txt"
TERMINOLOGY_FILE = "output/log/terminology.json"

def get_correction_prompt(text, terms_list):
    terms_str = ", ".join(terms_list)
    prompt = f"""
### Role
You are a professional ASR (Automatic Speech Recognition) correction expert in the medical/orthodontic domain.

### Task
You are given a text of 1000 words. Whisper ASR might have misrecognized some professional terms due to homophones (phonetically similar words).
Your job is to identify misrecognized words and propose corrections.

### Professional Terminology List (Reference):
[{terms_str}]

### ABSOLUTE RULES
1. YOU MUST NOT EDIT THE TEXT DIRECTLY.
2. You must ONLY output a JSON array of correction contracts.
3. If no errors are found, return an empty array [].
4. Only correct words that sound highly similar but are contextually wrong (e.g. "buckle" -> "buccal"). DO NOT rephrase sentences!

### Input Text
<text>
{text}
</text>

### Output Contract Format
Provide a JSON object containing a "corrections" array.
```json
{{
    "corrections": [
        {{
            "original_word": "buckle",
            "corrected_word": "buccal",
            "context_snippet": "attach it to the buckle tube",
            "reason": "Phonetically similar, buccal is the correct anatomical term."
        }}
    ]
}}
```

### Answer:
"""
    return prompt.strip()

def extract_terms_list():
    terms = []
    if os.path.exists(TERMINOLOGY_FILE):
        try:
            with open(TERMINOLOGY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'terms' in data:
                    terms = [t.get('src', '') for t in data['terms']]
        except Exception:
            pass
    return [t for t in terms if t]

def apply_corrections(text, corrections):
    # Programmatic replacement
    for c in corrections:
        snippet = c.get("context_snippet", "")
        orig = c.get("original_word", "")
        corr = c.get("corrected_word", "")
        if snippet and orig and corr:
            # Check if snippet actually exists in text
            if snippet in text:
                # Find the original word inside the snippet
                # Use regex bounds to replace whole word safely
                fixed_snippet = re.sub(rf'\b{re.escape(orig)}\b', corr, snippet, flags=re.IGNORECASE)
                text = text.replace(snippet, fixed_snippet)
                print(f"✅ Applied ASR correction: {orig} -> {corr} (Snippet: '{snippet}')")
            else:
                print(f"⚠️ Could not find context snippet for {orig}->{corr}: '{snippet}'")
    return text

def asr_correction_main():
    print("Starting ASR Error Correction phase...")
    if not os.path.exists(PUNCTUATED_TEXT_FILE):
        return

    terms_list = extract_terms_list()
    if not terms_list:
        print("No terminology found. Skipping ASR correction to save tokens.")
        return

    with open(PUNCTUATED_TEXT_FILE, 'r', encoding='utf-8') as f:
        full_text = f.read()

    words = full_text.split()
    batch_size = 1000
    batches = []

    current_batch = []
    for word in words:
        current_batch.append(word)
        if len(current_batch) >= batch_size and word.endswith('.'):
            batches.append(" ".join(current_batch))
            current_batch = []
    if current_batch:
        batches.append(" ".join(current_batch))

    def valid_contract(response_data):
        if "corrections" not in response_data or not isinstance(response_data["corrections"], list):
            return {"status": "error", "message": "Missing or invalid 'corrections' array"}
        return {"status": "success", "message": "Success"}

    corrected_batches = []
    for idx, batch in enumerate(batches):
        print(f"Scanning for ASR errors in batch {idx+1}/{len(batches)}...")
        prompt = get_correction_prompt(batch, terms_list)
        try:
            response = ask_gpt(prompt, response_json=True, log_title=f'asr_correction_{idx}', valid_def=valid_contract, reasoning_effort='high')
            corrections = response.get("corrections", [])
            if corrections:
                batch = apply_corrections(batch, corrections)
        except Exception as e:
            print(f"Error during ASR correction API call: {e}")

        corrected_batches.append(batch)

    full_corrected_text = " ".join(corrected_batches)
    with open(PUNCTUATED_TEXT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_corrected_text)

    print("ASR correction completed.")

if __name__ == '__main__':
    asr_correction_main()
