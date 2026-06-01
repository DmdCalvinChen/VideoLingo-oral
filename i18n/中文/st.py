import streamlit as st
import os, sys
from st_components.imports_and_utils import *
from core.config_utils import load_key

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="AuraSub", page_icon="docs/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"

def text_processing_section():
    st.header("翻译和生成字幕")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        此阶段包含以下步骤：
        <p style='font-size: 20px;'>
            1. WhisperX 逐字转录<br>
            2. 使用 NLP 和 LLM 进行句子分割<br>
            3. 总结和多步翻译<br>
            4. 切割和对齐长字幕<br>
            5. 生成时间轴和字幕<br>
            6. 将字幕合并到视频中
        """, unsafe_allow_html=True)

        if not os.path.exists(SUB_VIDEO):
            if st.button("开始处理字幕", key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            if load_key("resolution") != "0x0":
                st.video(SUB_VIDEO)
            download_subtitle_zip_button(text="下载所有字幕")
            
            if st.button("归档到'历史记录'", key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    with st.spinner("使用 Whisper 进行转录中..."):
        step2_whisperX.transcribe()
    with st.spinner("分割长句中..."):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
    with st.spinner("总结和翻译中..."):
        step4_1_summarize.get_summary()
        if load_key("pause_before_translate"):
            input("⚠️ 翻译前暂停。请前往 `output/log/terminology.json` 编辑术语。完成后按回车继续...")
        step4_2_translate_all.translate_all()
    with st.spinner("处理和对齐字幕中..."): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    with st.spinner("将字幕合并到视频中..."):
        step7_merge_sub_to_vid.merge_subtitles_to_video()
    
    st.success("字幕处理完成！🎉")
    st.balloons()

def audio_processing_section():
    st.header("配音")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        此阶段包含以下步骤：
        <p style='font-size: 20px;'>
            1. 生成音频任务和分段<br>
            2. 提取参考音频<br>
            3. 生成和合并音频文件<br>
            4. 将最终音频合并到视频中
        """, unsafe_allow_html=True)
        if not os.path.exists(DUB_VIDEO):
            if st.button("开始处理音频", key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success("音频处理完成！你可以在 `output` 文件夹中查看音频文件。")
            if load_key("resolution") != "0x0": 
                st.video(DUB_VIDEO) 
            if st.button("删除配音文件", key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button("归档到'历史记录'", key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner("生成音频任务中"): 
        step8_1_gen_audio_task.gen_audio_task_main()
        step8_2_gen_dub_chunks.gen_dub_chunks()
    with st.spinner("提取参考音频中"):
        step9_extract_refer_audio.extract_refer_audio_main()
    with st.spinner("生成所有音频中"):
        step10_gen_audio.gen_audio()
    with st.spinner("合并完整音频中"):
        step11_merge_full_audio.merge_full_audio()
    with st.spinner("将配音合并到视频中"):
        step12_merge_dub_to_vid.merge_video_audio()
    
    st.success("音频处理完成！🎇")
    st.balloons()

def main():
    st.markdown("<h1 style='text-align: center; color: #144070; margin-bottom: 30px;'>AuraSub</h1>", unsafe_allow_html=True)
    st.markdown(button_style, unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    text_processing_section()
    audio_processing_section()

if __name__ == "__main__":
    main()
