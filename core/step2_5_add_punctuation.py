import sys, os
import pandas as pd
import json
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt

CLEANED_CHUNKS_FILE = "output/log/cleaned_chunks.xlsx"
PUNCTUATED_TEXT_FILE = "output/log/punctuated_text.txt"

def strip_punctuation(text):
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def add_punctuation(words, previous_anchor=""):
    raw_text = " ".join(words)

    anchor_prompt = ""
    if previous_anchor:
        anchor_prompt = f"""
### CONTEXT ANCHOR (FROM PREVIOUS BATCH)
The previous text ended with this sentence: "{previous_anchor}"
Your task is to continue the punctuation from here. DO NOT include the anchor in your final output, but use it to understand if the first few words of this new batch belong to the previous sentence or start a new one.
"""

    prompt = f"""
### Role
You are an expert transcriber and linguist.

### Task
You will be provided with a raw stream of words without any punctuation. Your task is to add appropriate punctuation (commas, periods, question marks, etc.) and capitalization to make the text grammatically correct and highly readable.
{anchor_prompt}

### ABSOLUTE RULE: DO NOT ADD OR REMOVE ANY WORDS
You must use the EXACT same words in the EXACT same order.
If you change a single word, omit a word, or add a word, the alignment process will fail entirely.

### Input Words
<words>
{raw_text}
</words>

### Output Format
Provide a JSON object with a single key "punctuated_text" containing the final string.
```json
{{
    "punctuated_text": "This is a punctuated sentence."
}}
```

### Answer:
"""
    expected_words_cleaned = strip_punctuation(raw_text)

    def valid_punctuation(response_data):
        if "punctuated_text" not in response_data:
            return {"status": "error", "message": "Missing punctuated_text key"}
        result_text = response_data["punctuated_text"]
        result_cleaned = strip_punctuation(result_text)
        if result_cleaned != expected_words_cleaned:
            return {"status": "error", "message": "The words do not strictly match the input words after stripping punctuation. Please try again and strictly adhere to the ABSOLUTE RULE."}
        return {"status": "success", "message": "Success"}

    try:
        response = ask_gpt(prompt, response_json=True, log_title='punctuation', valid_def=valid_punctuation, reasoning_effort='low')
        return response["punctuated_text"]
    except Exception as e:
        print(f"Error during punctuation API call: {e}")
        return raw_text

def get_last_sentence(text):
    # Extremely simple heuristic to grab the last chunk of punctuated text as an anchor
    sentences = re.split(r'(?<=[.!?]) +', text)
    if sentences:
        return sentences[-1]
    return text[-100:]

def add_punctuation_main():
    print("Starting LLM punctuation phase with sliding anchor...")
    if not os.path.exists(CLEANED_CHUNKS_FILE):
        return
    df = pd.read_excel(CLEANED_CHUNKS_FILE)
    words = df['text'].apply(lambda x: str(x).strip('"')).tolist()

    # Using 1000 words per batch for cost/context efficiency
    batch_size = 1000
    word_batches = [words[i:i + batch_size] for i in range(0, len(words), batch_size)]

    all_punctuated_text = []
    previous_anchor = ""

    for idx, batch in enumerate(word_batches):
        print(f"Adding punctuation to batch {idx+1}/{len(word_batches)}...")
        punctuated_batch = add_punctuation(batch, previous_anchor)
        all_punctuated_text.append(punctuated_batch)
        previous_anchor = get_last_sentence(punctuated_batch)

    full_text = " ".join(all_punctuated_text)
    os.makedirs(os.path.dirname(PUNCTUATED_TEXT_FILE), exist_ok=True)
    with open(PUNCTUATED_TEXT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_text)

if __name__ == '__main__':
    add_punctuation_main()
