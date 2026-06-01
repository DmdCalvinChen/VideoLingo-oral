<div align="center">

# AuraSub
**Precision-Driven Semantic Translation & Dubbing for Professional Content**

[**English**](/README.md)｜[**中文**](/i18n/README.zh.md)

</div>

## 🌟 Overview

**AuraSub** is an advanced, independent evolution of the original VideoLingo project. Unlike generic translation tools aimed at casual entertainment, AuraSub is explicitly engineered for **professional knowledge sharing, academic lectures, and hardcore technical tutorials**.

It focuses heavily on precise semantic sentence breaking and strict adherence to the **Netflix single-line subtitle standard (absolutely no double-line subtitles)**. By completely replacing legacy mechanical NLP segmentations with a pure Zero-Loss LLM architecture, AuraSub ensures contextually flawless translations that are perfectly synced to the original audio timestamps at the millisecond level.

### Core Features:
- 🎥 **Video Ingestion:** Direct video download via yt-dlp.
- **🎙️ Word-Level Subtitle Recognition:** Powered by WhisperX for low-illusion, precise word-level timestamping.
- **🧠 Zero-Loss LLM Semantic Chunking:** Replaces mechanical NLP (e.g., SpaCy) with intelligent LLM-driven punctuation and logic-based chunking. It reads and structures exact word outputs natively, preventing vocabulary loss.
- **📚 Context-Aware Paragraph Translation & Regex Terminology:** Groups sub-clauses naturally into paragraph-level prompts. It uses strict regex word-boundary matching for custom terminology injection, preventing LLM hallucinations (e.g., confusing "buckle" with "buccal"), and allowing free linguistic restructuring while maintaining perfect meaning.
- **🪡 Robust Two-Pointer Alignment:** A custom alignment engine mathematically matches translated blocks back to their precise word-level audio timestamps, entirely eliminating the missing timeline issues of previous iterations.
- **✅ Netflix-Standard Exclusivity:** Enforces strict single-line subtitles only, guaranteeing a clean, professional viewing experience.
- **🗣️ Advanced Dubbing:** Seamless integration with GPT-SoVITS, Azure, OpenAI TTS, Fish-TTS, and more.
- 🚀 **Streamlit UI:** One-click startup and processing interface.

## 🎥 Demo

<table>
<tr>
<td width="50%">

### Translation Quality Demonstration
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="50%">

### High-Quality Dubbing (GPT-SoVITS)
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### Language Support

**Input Languages:**
🇺🇸 English | 🇷🇺 Russian | 🇫🇷 French | 🇩🇪 German | 🇮🇹 Italian | 🇪🇸 Spanish | 🇯🇵 Japanese | 🇨🇳 Chinese

**Translation & Dubbing:**
Translation supports practically all languages powered by leading LLMs. Dubbing support depends on the chosen TTS provider.

## Installation

> **Note:** To use NVIDIA GPU acceleration on Windows, please complete the following steps first:
> 1. Install [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. Install [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. Add `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` to your system PATH
> 4. Restart your computer

> **Note:** FFmpeg is required. Please install it via package managers:
> - Windows: ```choco install ffmpeg``` (via [Chocolatey](https://chocolatey.org/))
> - macOS: ```brew install ffmpeg``` (via [Homebrew](https://brew.sh/))
> - Linux: ```sudo apt install ffmpeg``` (Debian/Ubuntu) or ```sudo dnf install ffmpeg``` (Fedora)

1. Clone the repository

```bash
git clone https://github.com/YourOrg/AuraSub.git
cd AuraSub
```

2. Install dependencies (requires `python=3.10`)

```bash
conda create -n aurasub python=3.10.0 -y
conda activate aurasub
python install.py
```

3. Start the application

```bash
streamlit run st.py
```

### Docker
Alternatively, you can use Docker (requires CUDA 12.4 and NVIDIA Driver version >550):

```bash
docker build -t aurasub .
docker run -d -p 8501:8501 --gpus all aurasub
```

## API Configuration
AuraSub supports OpenAI-like API formats for reasoning and translation:
- Supported LLMs: `claude-3-5-sonnet-20240620`, `gemini-2.0-flash-exp`, `gpt-4o`, `deepseek-v4-flash`, etc. (For processing, models with structured JSON adherence and reasoning capabilities are highly recommended).
- Supported TTS: `azure-tts`, `openai-tts`, `fish-tts`, `GPT-SoVITS`, `edge-tts`, and more.

## Current Limitations

1. WhisperX transcription performance may be affected by heavy background noise (using wav2vec alignment). For best results on professional content, clean audio tracks are preferred.
2. Due to strict JSON schema validation in the LLM pipeline, using weaker, non-reasoning LLMs may cause intermediate step failures. If this occurs, delete the `output` folder and retry with a stronger model (e.g., GPT-4o, Claude 3.5, or DeepSeek).
3. The dubbing feature synchronizes speaking rates dynamically, but language structural differences mean it may require manual tweaking for absolute perfection.
4. **Multilingual recognition** defaults to the primary detected language due to WhisperX's specialized single-language alignment constraint.

## 📄 License & Attribution

This project is licensed under the **Apache 2.0 License**.

**AuraSub** is an independent, heavily refactored fork and evolution of [VideoLingo](https://github.com/Huanshere/VideoLingo), originally created by **Huanshere**. We sincerely thank the original author for the foundational engineering architecture, which made this semantic-focused evolution possible.

Special thanks to the following open-source projects for their underlying capabilities:
[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)
