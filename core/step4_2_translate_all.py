import sys, os
import pandas as pd
import json
import concurrent.futures
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt
from core.config_utils import load_key
from core.step8_1_gen_audio_task import check_len_then_trim
from core.step6_generate_final_timeline import align_timestamp
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

SENTENCE_SPLIT_FILE = "output/log/sentence_splitbymeaning.txt"
TRANSLATION_RESULTS_FILE = "output/log/translation_results.xlsx"
TERMINOLOGY_FILE = "output/log/terminology.json"
CLEANED_CHUNKS_FILE = "output/log/cleaned_chunks.xlsx"

def get_paragraph_translation_prompt(paragraph, language, terminology_prompt=None):
    term_instruction = ""
    if terminology_prompt:
        term_instruction = f"### Terminology to use:\n{terminology_prompt}\n"

    prompt = f"""
### Role
You are an expert, professional translator from the source language to {language}.

### Task
You are given a paragraph consisting of numbered sentences. Your job is to translate the entire paragraph naturally, allowing you to reorder, restructure, and rephrase logic as needed across sentences to ensure the final output is native, fluent, and highly professional.
However, because this is for subtitles, you MUST map your final translated output back to the original numbered sentences.
If a sentence's meaning was combined with another, split the translation logically or repeat necessary parts so that every original sentence number has a corresponding translated sentence.

{term_instruction}
### Input Paragraph
<paragraph>
{paragraph}
</paragraph>

### Output Format
Provide a JSON object where the keys are the sentence numbers (as strings) and the values are the translated sentences.
```json
{{
    "1": "Translated sentence 1",
    "2": "Translated sentence 2"
}}
```

### Answer:
"""
    return prompt.strip()

def translate_paragraph(sentences_chunk, start_idx, language, theme_prompt=""):
    paragraph = "\n".join([f"{i+1}. {sentence}" for i, sentence in enumerate(sentences_chunk)])
    prompt = get_paragraph_translation_prompt(paragraph, language, theme_prompt)

    def valid_translation(response_data):
        if not isinstance(response_data, dict):
            return {"status": "error", "message": "Response must be a JSON dictionary."}
        if len(response_data) != len(sentences_chunk):
            return {"status": "error", "message": f"Expected {len(sentences_chunk)} keys, but got {len(response_data)}."}
        return {"status": "success", "message": "Success"}

    try:
        result = ask_gpt(prompt, response_json=True, log_title=f'translate_paragraph_{start_idx}', valid_def=valid_translation)
        translations = [result.get(str(i+1), "Translation error") for i in range(len(sentences_chunk))]
        return start_idx, translations
    except Exception as e:
        print(f"Error during translation chunk {start_idx}: {e}")
        return start_idx, [f"[Mock Translation]: {s}" for s in sentences_chunk]

def translate_all():
    if not os.path.exists(SENTENCE_SPLIT_FILE):
        console.print(f"Error: {SENTENCE_SPLIT_FILE} not found.")
        return

    if os.path.exists(TRANSLATION_RESULTS_FILE):
        console.print(Panel("🚨 File `translation_results.xlsx` already exists, skipping TRANSLATE ALL.", title="Warning", border_style="yellow"))
        return

    console.print("[bold green]Start Translating All...[/bold green]")
    with open(SENTENCE_SPLIT_FILE, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f.read().split('\n') if line.strip()]

    language = load_key("target_language") or "Simplified Chinese"
    theme_prompt = ""
    if os.path.exists(TERMINOLOGY_FILE):
        try:
            with open(TERMINOLOGY_FILE, 'r', encoding='utf-8') as f:
                theme_prompt = json.load(f).get('theme', "")
        except:
            pass

    chunk_size = 10
    sentence_chunks = [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Translating chunks...", total=len(sentence_chunks))
        with concurrent.futures.ThreadPoolExecutor(max_workers=load_key("max_workers")) as executor:
            futures = []
            for i, chunk in enumerate(sentence_chunks):
                future = executor.submit(translate_paragraph, chunk, i, language, theme_prompt)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                progress.update(task, advance=1)

    results.sort(key=lambda x: x[0])
    
    src_text = sentences
    trans_text = []
    for r in results:
        trans_text.extend(r[1])

    df_text = pd.read_excel(CLEANED_CHUNKS_FILE)
    df_text['text'] = df_text['text'].str.strip('"').str.strip()
    df_translate = pd.DataFrame({'Source': src_text, 'Translation': trans_text})
    subtitle_output_configs = [('trans_subs_for_audio.srt', ['Translation'])]

    df_time = align_timestamp(df_text, df_translate, subtitle_output_configs, output_dir=None, for_display=False)
    console.print(df_time)

    df_time['Translation'] = df_time.apply(lambda x: check_len_then_trim(x['Translation'], x['duration']) if x['duration'] > load_key("min_trim_duration") else x['Translation'], axis=1)
    console.print(df_time)
    
    df_time.to_excel(TRANSLATION_RESULTS_FILE, index=False)
    console.print("[bold green]✅ Translation completed and results saved.[/bold green]")

if __name__ == '__main__':
    translate_all()
