import sys, os
import pandas as pd
import json
import re
import string
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt
from core.config_utils import load_key

CLEANED_CHUNKS_FILE = "output/log/cleaned_chunks.xlsx"
PUNCTUATED_TEXT_FILE = "output/log/punctuated_text.txt"
CUSTOM_TERMS_PATH = "custom_terms.xlsx"

def get_correction_prompt(text, terms_list):
    terms_str = ", ".join(terms_list)
    prompt = f"""
### Role
You are a professional ASR (Automatic Speech Recognition) correction expert.

### Task
You are given a chunk of text. Whisper ASR might have misrecognized some words due to homophones (phonetically similar words).
Your job is to identify misrecognized words and propose corrections based on context.

### Professional Terminology List (Optional Reference):
[{terms_str}] (If empty, rely entirely on context to fix general phonetic errors).

### ABSOLUTE RULES
1. YOU MUST NOT EDIT THE TEXT DIRECTLY.
2. You must ONLY output a JSON array of correction contracts.
3. If no errors are found, return an empty array [].
4. Only correct words that sound highly similar but are contextually wrong (e.g. "buckle" -> "buccal"). DO NOT rephrase sentences!
5. Use the `apply_globally` flag wisely:
   - Set to `true` IF the error is a systematic misrecognition (e.g., a specific name or technical term misheard the same way throughout the text, like "macro" instead of "micro"). This will replace ALL instances of the word in the text.
   - Set to `false` IF the error is context-dependent (e.g., "to" instead of "two"). In this case, you MUST provide the exact `context_snippet` where it occurs so we only replace that specific instance.
6. Before you finish your reasoning, comprehensively review these absolute rules and ensure your output perfectly complies.

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
            "original_word": "macro",
            "corrected_word": "micro",
            "context_snippet": "induce macro fracture inside",
            "apply_globally": true,
            "reason": "Phonetically similar, systematic error for 'micro'."
        }},
        {{
            "original_word": "buckle",
            "corrected_word": "buccal",
            "context_snippet": "attach it to the buckle tube",
            "apply_globally": false,
            "reason": "Phonetically similar, buccal is the anatomical term."
        }}
    ]
}}
```

### Answer:
"""
    return prompt.strip()

def extract_terms_list():
    terms = []
    if os.path.exists(CUSTOM_TERMS_PATH):
        try:
            df = pd.read_excel(CUSTOM_TERMS_PATH)
            terms = [str(row.iloc[0]) for _, row in df.iterrows() if pd.notna(row.iloc[0])]
        except Exception as e:
            print(f"Failed to read {CUSTOM_TERMS_PATH}: {e}")
    return [t for t in terms if t.strip()]

def apply_corrections(text, corrections, df_words):
    # Use a static list of original words for reliable index searching
    original_df_words_list = df_words['text'].apply(lambda x: str(x).strip('"').strip(string.punctuation).lower()).tolist()
    
    for c in corrections:
        orig = c.get("original_word", "")
        corr = c.get("corrected_word", "")
        apply_globally = c.get("apply_globally", False)
        snippet = c.get("context_snippet", "")
        
        if not orig or not corr:
            continue
            
        orig_words = [w.strip(string.punctuation).lower() for w in orig.split() if w.strip(string.punctuation)]
        if not orig_words:
            continue

        if apply_globally:
            # 1. Update text globally
            text = re.sub(rf'\b{re.escape(orig)}\b', corr, text, flags=re.IGNORECASE)
            
            # 2. Update df_words globally
            matches_found = 0
            for i in range(len(original_df_words_list) - len(orig_words) + 1):
                if original_df_words_list[i:i+len(orig_words)] == orig_words:
                    first_idx = i
                    last_idx = i + len(orig_words) - 1
                    
                    first_orig = str(df_words.at[first_idx, 'text'])
                    last_orig = str(df_words.at[last_idx, 'text'])
                    
                    m_lead = re.match(r'^([^\w\s]+)', first_orig)
                    lead_p = m_lead.group(1) if m_lead else ""
                    
                    m_trail = re.search(r'([^\w\s]+)$', last_orig)
                    trail_p = m_trail.group(1) if m_trail else ""
                    
                    df_words.at[first_idx, 'text'] = lead_p + corr + trail_p
                    for clear_idx in range(first_idx + 1, last_idx + 1):
                        df_words.at[clear_idx, 'text'] = ""
                    matches_found += 1
            if matches_found > 0:
                print(f"✅ Applied ASR correction (GLOBALLY, {matches_found} times): {orig} -> {corr}")
            else:
                print(f"⚠️ Global correction {orig}->{corr} found 0 matches in timeline.")
                
        else:
            # Context specific
            if snippet and snippet in text:
                # 1. Update text within snippet
                fixed_snippet = re.sub(rf'\b{re.escape(orig)}\b', corr, snippet, flags=re.IGNORECASE)
                text = text.replace(snippet, fixed_snippet)
                
                # 2. Update df_words
                snippet_words = [w.strip(string.punctuation).lower() for w in snippet.split() if w.strip(string.punctuation)]
                
                for i in range(len(original_df_words_list) - len(snippet_words) + 1):
                    if original_df_words_list[i:i+len(snippet_words)] == snippet_words:
                        # Find orig within snippet
                        for k in range(len(snippet_words) - len(orig_words) + 1):
                            if snippet_words[k:k+len(orig_words)] == orig_words:
                                first_idx = i + k
                                last_idx = i + k + len(orig_words) - 1
                                
                                first_orig = str(df_words.at[first_idx, 'text'])
                                last_orig = str(df_words.at[last_idx, 'text'])
                                
                                m_lead = re.match(r'^([^\w\s]+)', first_orig)
                                lead_p = m_lead.group(1) if m_lead else ""
                                
                                m_trail = re.search(r'([^\w\s]+)$', last_orig)
                                trail_p = m_trail.group(1) if m_trail else ""
                                
                                df_words.at[first_idx, 'text'] = lead_p + corr + trail_p
                                for clear_idx in range(first_idx + 1, last_idx + 1):
                                    df_words.at[clear_idx, 'text'] = ""
                                break
                        break
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
        print("No custom terminology found. Proceeding with general context-based ASR correction.")
    else:
        print(f"📖 Custom Terms Loaded: {len(terms_list)} terms")

    with open(PUNCTUATED_TEXT_FILE, 'r', encoding='utf-8') as f:
        full_text = f.read()
        
    df_words = pd.read_excel(CLEANED_CHUNKS_FILE)

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
        if len(batches) > 0 and len(current_batch) < 200:
            batches[-1] += " " + " ".join(current_batch)
        else:
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
                batch = apply_corrections(batch, corrections, df_words)
        except Exception as e:
            print(f"Error during ASR correction API call: {e}")

        corrected_batches.append(batch)

    full_corrected_text = " ".join(corrected_batches)
    with open(PUNCTUATED_TEXT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_corrected_text)
        
    df_words.to_excel(CLEANED_CHUNKS_FILE, index=False)

    print("ASR correction completed.")

if __name__ == '__main__':
    asr_correction_main()
