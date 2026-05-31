import sys, os
import pandas as pd
import json
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt

PUNCTUATED_TEXT_FILE = "output/log/punctuated_text.txt"
SENTENCE_TXT_PATH = 'output/log/sentence_splitbymeaning.txt'

def strip_all_formatting(text):
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def mechanical_fallback_split(text):
    words = text.split()
    sentences = []
    chunk = []
    for w in words:
        chunk.append(w)
        if len(chunk) >= 15:
            sentences.append(" ".join(chunk))
            chunk = []
    if chunk:
        sentences.append(" ".join(chunk))
    return sentences

def chunk_punctuated_text(text):
    prompt = f"""
### Role
You are a professional subtitle formatting expert.

### Task
You are given an English transcript of a video. The text already has proper punctuation.
Your task is to split this text into logically complete subtitle sentences, where each sentence contains ideally between 12 and 22 words (never exceeding 25 words).

### Instructions
1. Break the text into individual subtitle lines.
2. If a sentence is very long, break it into logical clauses.
3. Provide one sentence per line.
4. ABSOLUTE RULE: DO NOT add, remove, or modify any words. Just determine the breaks.

### Input Text
<text>
{text}
</text>

### Output Format
Provide a JSON object with a single key "sentences" containing a list of strings, where each string is one formatted subtitle line.
```json
{{
    "sentences": [
        "First logically broken sentence here.",
        "Second logically broken sentence continues here."
    ]
}}
```

### Answer:
"""
    expected_cleaned = strip_all_formatting(text)
    def valid_chunking(response_data):
        if "sentences" not in response_data:
            return {"status": "error", "message": "Missing sentences key"}
        result_text = " ".join(response_data["sentences"])
        result_cleaned = strip_all_formatting(result_text)
        if result_cleaned != expected_cleaned:
            return {"status": "error", "message": "The words do not strictly match the input words after stripping punctuation. Please try again and strictly adhere to the ABSOLUTE RULE."}
        for sent in response_data["sentences"]:
            word_count = len(sent.split())
            if word_count > 25:
                return {"status": "error", "message": f"Sentence '{sent}' exceeds 25 words ({word_count} words). Please keep all lines under 25 words."}
        return {"status": "success", "message": "Success"}

    try:
        response = ask_gpt(prompt, response_json=True, log_title='logical_chunking', valid_def=valid_chunking, reasoning_effort='high')
        return response["sentences"]
    except Exception as e:
        print(f"Error during logical chunking API call: {e}")
        return mechanical_fallback_split(text)

def split_by_semantic_chunking():
    print("Starting LLM logical chunking phase...")
    if not os.path.exists(PUNCTUATED_TEXT_FILE):
        return
    with open(PUNCTUATED_TEXT_FILE, 'r', encoding='utf-8') as f:
        full_text = f.read()

    words = full_text.split()
    batch_size = 350
    word_batches = []
    current_batch = []
    for word in words:
        current_batch.append(word)
        if len(current_batch) >= batch_size and word.endswith('.'):
            word_batches.append(" ".join(current_batch))
            current_batch = []
    if current_batch:
        word_batches.append(" ".join(current_batch))

    all_sentences = []
    for idx, batch in enumerate(word_batches):
        print(f"Logically chunking batch {idx+1}/{len(word_batches)}...")
        sentences = chunk_punctuated_text(batch)
        all_sentences.extend(sentences)

    os.makedirs(os.path.dirname(SENTENCE_TXT_PATH), exist_ok=True)
    with open(SENTENCE_TXT_PATH, 'w', encoding='utf-8') as f:
        for sentence in all_sentences:
            f.write(f"{sentence}\n")

if __name__ == '__main__':
    split_by_semantic_chunking()
