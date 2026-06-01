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

def add_punctuation(words, previous_anchor="", next_preview=""):
    raw_text = " ".join(words)

    anchor_prompt = ""
    if previous_anchor:
        anchor_prompt = f"""
### CONTEXT ANCHOR (FROM PREVIOUS BATCH)
The previous text ended with this sentence: "{previous_anchor}"
Your task is to continue the punctuation from here. DO NOT include the anchor in your final output, but use it to understand if the first few words of this new batch belong to the previous sentence or start a new one.
"""

    lookahead_prompt = ""
    if next_preview:
        lookahead_prompt = f"""
### LOOK-AHEAD CONTEXT (NEXT BATCH PREVIEW)
The next batch starts with these words: "{next_preview}"
CRITICAL INSTRUCTION: If the last words of the current batch form an incomplete sentence that seamlessly continues into the NEXT BATCH PREVIEW, you MUST NOT put a period or any ending punctuation at the end of your output. 
DO NOT include these preview words in your output. Only punctuate the <words> provided below.
"""

    prompt = f"""
### Role
You are an expert transcriber and linguist.

### Task
You will be provided with a raw stream of words without any punctuation. Your task is to add appropriate punctuation (commas, periods, question marks, etc.) and capitalization to make the text grammatically correct and highly readable.
{anchor_prompt}
{lookahead_prompt}

### ABSOLUTE RULE: DO NOT ADD, REMOVE, OR MODIFY ANY WORDS
You must use the EXACT same words in the EXACT same order.
If you change a single word, omit a word, or add a word, the alignment process will fail entirely.
Examples of STRICT FORBIDDEN actions:
1. DO NOT remove filler words:
   - Original: "uh yes i agree"
   - Correct: "Uh, yes, I agree."
   - FORBIDDEN: "Yes, I agree." (Do not remove "uh")
2. DO NOT fix grammatical errors:
   - Original: "he go to school every day"
   - Correct: "He go to school every day."
   - FORBIDDEN: "He goes to school every day." (Do not fix "go" to "goes")
3. DO NOT fix misspellings or wrong words (even if obvious):
   - Original: "welcome to macro soft"
   - Correct: "Welcome to macro soft."
   - FORBIDDEN: "Welcome to Microsoft." (Do not fix "macro soft" to "Microsoft")

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
        
        # Check if the LLM actually added punctuation (prevent laziness)
        punctuation_count = result_text.count('.') + result_text.count('?') + result_text.count('!')
        if punctuation_count < len(expected_words_cleaned.split()) / 50:
            return {"status": "error", "message": "You failed to add sufficient ending punctuation (periods, question marks). Please properly punctuate the ENTIRE text."}
            
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

    # Using 400 words per batch for punctuation to prevent LLM laziness/hallucinations on huge text walls
    batch_size = 400
    word_batches = [words[i:i + batch_size] for i in range(0, len(words), batch_size)]
    
    # Merge orphan batch: if the last batch is too small (< 100 words), merge it into the previous one
    if len(word_batches) > 1 and len(word_batches[-1]) < 100:
        word_batches[-2].extend(word_batches[-1])
        word_batches.pop()

    all_punctuated_text = []
    previous_anchor = ""

    overlap_size = 30  # Number of words to preview from the next batch
    for idx, batch in enumerate(word_batches):
        print(f"Adding punctuation to batch {idx+1}/{len(word_batches)}...")
        # Build look-ahead preview from the next batch
        next_preview = ""
        if idx < len(word_batches) - 1:
            next_preview = " ".join(word_batches[idx + 1][:overlap_size])
        punctuated_batch = add_punctuation(batch, previous_anchor, next_preview)
        all_punctuated_text.append(punctuated_batch)
        previous_anchor = get_last_sentence(punctuated_batch)

    full_text = " ".join(all_punctuated_text)
    os.makedirs(os.path.dirname(PUNCTUATED_TEXT_FILE), exist_ok=True)
    with open(PUNCTUATED_TEXT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_text)

if __name__ == '__main__':
    add_punctuation_main()
