<div align="center">

# AuraSub
**面向专业内容的极致语义翻译与配音利器**

[**English**](/README.md)｜[**中文**](/i18n/README.zh.md)

</div>

## 🌟 简介

**AuraSub** 是对原 VideoLingo 项目的一次深度重构与独立演进。与市面上主打“通用娱乐翻译”的工具截然不同，AuraSub 是专门为**专业知识分享、学术演讲、硬核技术教程**量身打造的翻译利器。

我们极致追求**精确的语义断句**，并强制执行**Netflix 标准的单行字幕显示（绝无双行字幕出现）**。通过彻底淘汰传统的机器 NLP（如 SpaCy）物理切片，AuraSub 引入了基于大语言模型（LLM）的“零损耗语义切分架构”，确保了在毫秒级精确对齐原始音频时间戳的同时，呈现出上下文完美连贯的专业翻译。

### 核心特性：
- 🎥 **视频抓取：** 使用 yt-dlp 直接下载 YouTube 等视频源。
- **🎙️ 单词级精准底座：** 使用 WhisperX 提取极低幻觉、精确到词级别的底层时间戳。
- **🧠 零损耗大模型语义断句：** 彻底抛弃传统 NLP 机械切分。利用 LLM 在保留所有原词的基础上，智能进行标点推断与逻辑从句切分，从根本上防止词汇丢失与时间轴错乱。
- **📚 正则级术语控制与段落级翻译：** 打破死板的逐句翻译，将切分好的逻辑语义块按段落打包送入 LLM。引入**精确的正则表达式单词边界（Regex Word Boundaries）**术语匹配，彻底杜绝音近词引发的大模型幻觉（如将 buckle 误识为 buccal），让 LLM 在跨语言重构语序时既能意译，又能保持专业名词的绝对严谨。
- **🪡 强效双指针时间轴对齐：** 通过精心设计的单词级双指针匹配算法，将翻译好的长句1:1无损绑定回底层的时间戳，彻底消灭了以往版本中的“翻译丢失时间轴”报错。
- **✅ 坚守 Netflix 单行标准：** 强制控制输出格式，绝无双行字幕，提供极其干净、专业的学术级观影体验。
- **🗣️ 多平台高质量配音：** 无缝对接 GPT-SoVITS、Azure、OpenAI TTS、Fish-TTS 等行业顶尖配音方案。
- 🚀 **Streamlit 极简交互：** 一键启动，流程清晰。

## 🎥 效果演示

<table>
<tr>
<td width="50%">

### 高质量专业翻译演示
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="50%">

### GPT-SoVITS 高级配音
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### 语言支持

**输入语言：**
🇺🇸 英语 | 🇷🇺 俄语 | 🇫🇷 法语 | 🇩🇪 德语 | 🇮🇹 意大利语 | 🇪🇸 西班牙语 | 🇯🇵 日语 | 🇨🇳 中文

**翻译与配音：**
翻译支持所有主流 LLM 所涵盖的语言。配音语言的支持情况取决于您所选择的 TTS 接口类型。

## 安装

> **注意:** 在 Windows 上使用 NVIDIA GPU 加速需要先完成以下步骤:
> 1. 安装 [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. 安装 [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. 将 `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` 添加到系统环境变量 PATH 中
> 4. 重启电脑

> **注意:** FFmpeg 是必需的，请通过包管理器安装：
> - Windows：```choco install ffmpeg```（通过 [Chocolatey](https://chocolatey.org/)）
> - macOS：```brew install ffmpeg```（通过 [Homebrew](https://brew.sh/)）
> - Linux：```sudo apt install ffmpeg```（Debian/Ubuntu）或 ```sudo dnf install ffmpeg```（Fedora）

1. 克隆仓库

```bash
git clone https://github.com/YourOrg/AuraSub.git
cd AuraSub
```

2. 安装依赖（需要 `python=3.10`）

```bash
conda create -n aurasub python=3.10.0 -y
conda activate aurasub
python install.py
```

3. 启动应用

```bash
streamlit run st.py
```

### Docker
还可以选择使用 Docker（要求 CUDA 12.4 和 NVIDIA Driver 版本 >550）：

```bash
docker build -t aurasub .
docker run -d -p 8501:8501 --gpus all aurasub
```

## API 配置
AuraSub 支持 OpenAI-Like 格式的 API 调用，用于驱动核心的语义切分与翻译引擎：
- 推荐使用具备较强结构化 JSON 输出和推理能力的大模型：`claude-3-5-sonnet-20240620`, `gpt-4o`, `deepseek-v4-flash`, `gemini-2.0-flash-exp` 等。
- 配音(TTS)接口支持：`azure-tts`, `openai-tts`, `fish-tts`, `GPT-SoVITS`, `edge-tts` 等。

## 当前限制
1. WhisperX 底层转录（wav2vec对齐）对重度背景噪音较敏感。对于专业领域内容，建议输入音轨较为纯净的视频，或者前置开启人声分离。
2. 整个处理管线高度依赖 LLM 返回的严格 JSON 格式化数据，如果使用较弱或不具备深度思考能力的模型，容易在中间过程因解析错误而中断。若发生此情况，请删除 `output` 文件夹并更换更强的模型重新运行。
3. 动态语速匹配虽已做了工程优化，但在语言长度结构差异极大的语种对之间，TTS 配音依然可能需要少量的人工微调。
4. **多语言视频转录识别**：受限于 WhisperX 强制对齐单词级字幕时使用的是单语言特化模型，当前流程默认仅保留并识别主要语言。

## 📄 许可证与鸣谢

本项目采用 **Apache 2.0 许可证** 开源。

**AuraSub** 是基于原开源项目 [VideoLingo](https://github.com/Huanshere/VideoLingo) 的一次独立演进（Fork/Derivative Work）。原项目由 **Huanshere** 创立，我们在此向原作者表示最诚挚的感谢——是 VideoLingo 优秀的底层工程架构，孕育了如今以“专注语义与专业翻译”为核心理念的 AuraSub。

同时，衷心感谢以下开源项目为本工具底层能力提供的支持：
[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)
