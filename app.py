import streamlit as st
import google.generativeai as genai
import json
import asyncio
import edge_tts
import os
import shutil
import time
from moviepy.editor import VideoFileClip, AudioFileClip

# 1. កំណត់ទម្រង់វេបសាយ
st.set_page_config(page_title="Auto Video Dubbing Studio", layout="wide", page_icon="🎬")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1565C0; color: white; font-weight: bold; height: 3em; }
    .dub-container { border-left: 5px solid #1565C0; padding: 15px; border-radius: 4px; margin-bottom: 10px; background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .speaker-tag { background-color: #E3F2FD; color: #1565C0; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1565C0;'>🎬 AI Full Video Dubbing Studio (Khmer V3)</h1>", unsafe_allow_html=True)

# របារចំហៀង
st.sidebar.title("⚙️ ការកំណត់សំឡេង និង API")
api_key = st.sidebar.text_input("🔑 Gemini API Key:", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("🎭 កំណត់ល្បឿនសំឡេង")
voice_speed = st.sidebar.slider("ល្បឿននិយាយ (Rate):", min_value=-50, max_value=50, value=0, step=5, format="%d%%")
speed_string = f"{voice_speed:+d}%" if voice_speed != 0 else "+0%"

if api_key:
    genai.configure(api_key=api_key)
else:
    st.sidebar.warning("⚠️ សូមបញ្ចូល API Key ដើម្បីបន្ត")

# មុខងារជំនួយបង្កើតសំឡេងទាំងអស់ព្រមគ្នា
async def generate_all_audio_v3(dubbing_data, speed):
    if os.path.exists("audio_chunks"):
        shutil.rmtree("audio_chunks")
    os.makedirs("audio_chunks")
    
    tasks = []
    for index, item in enumerate(dubbing_data):
        output_path = f"audio_chunks/voice_{index}.mp3"
        gender = item.get("speaker_gender", "Male").lower()
        voice = "km-KH-SreyrathNeural" if gender == "female" else "km-KH-PisethNeural"
        
        communicate = edge_tts.Communicate(item['khmer_text'], voice, rate=speed)
        tasks.append(communicate.save(output_path))
    
    await asyncio.gather(*tasks)

# មុខងារសម្រាប់កែសម្រួលសំឡេងទោល
async def generate_single_audio_v3(text, voice_type, speed, output_path):
    voice = "km-KH-SreyrathNeural" if voice_type == "ស្រី (Sreyrath)" else "km-KH-PisethNeural"
    communicate = edge_tts.Communicate(text, voice, rate=speed)
    await communicate.save(output_path)

# 2. ផ្នែកបង្ហោះវីដេអូ
uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូដើម (MP4)", type=["mp4"])

if uploaded_file and api_key:
    video_path = "input_video.mp4"
    
    if 'current_video' not in st.session_state or st.session_state['current_video'] != uploaded_file.name:
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())
        st.session_state['current_video'] = uploaded_file.name
        if 'dubbing_data' in st.session_state:
            del st.session_state['dubbing_data']

    col_video, col_sub = st.columns([1, 1.3])

    with col_video:
        st.subheader("📹 វីដេអូដើម")
        st.video(video_path)
        
        if st.button("🚀 ចាប់ផ្ដើមផលិតវីដេអូសំឡេងខ្មែរ"):
            with st.status("កំពុងដំណើរការផលិតវីដេអូ...", expanded=True) as status:
                try:
                    st.write("📥 កំពុង Upload វីដេអូទៅកាន់ Gemini...")
                    raw_video = genai.upload_file(path=video_path)
                    
                    st.write("⏳ ទុកពេលឱ្យ Google រៀបចំស្ថានភាពហ្វាយ (ACTIVE)...")
                    while raw_video.state.name == "PROCESSING":
                        time.sleep(5)
                        raw_video = genai.get_file(raw_video.name)
                    
                    st.write("🧠 Gemini កំពុងបំបែកតួអង្គ និងបកប្រែជាភាសាខ្មែរ...")
                    model = genai.GenerativeModel(
                        model_name="gemini-2.5-flash",
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    prompt = """
                    Analyze this video. Correctly identify the timeline of speech. 
                    Translate English into professional, natural Khmer suitable for dubbing.
                    Also detect if the speaker at that moment is Male or Female.
                    Output strictly in this JSON array format:
                    [
                      {
                        "start_time": "HH:MM:SS",
                        "end_time": "HH:MM:SS",
                        "speaker_gender": "Male or Female",
                        "english_text": "English text",
                        "khmer_text": "ឃ្លាបកប្រែខ្មែរ"
                      }
                    ]
                    """
                    
                    response = model.generate_content([raw_video, prompt])
                    st.session_state['dubbing_data'] = json.loads(response.text)
                    
                    st.write("🗣️ កំពុងបង្កើតសំឡេង AI ភាសាខ្មែរ...")
                    asyncio.run(generate_all_audio_v3(st.session_state['dubbing_data'], speed_string))
                    
                    # ✨ មុខងារពិសេស៖ ផ្គុំសំឡេងខ្មែរទាំងអស់បញ្ចូលគ្នាជាហ្វាយតែមួយ
                    st.write("📦 កំពុងរៀបចំប្រព័ន្ធសំឡេងរួម...")
                    full_audio_path = "full_khmer_voiceover.mp3"
                    with open(full_audio_path, "wb") as outfile:
                        for i in range(len(st.session_state['dubbing_data'])):
                            chunk_path = f"audio_chunks/voice_{i}.mp3"
                            if os.path.exists(chunk_path):
                                with open(chunk_path, "rb") as infile:
                                    outfile.write(infile.read())
                    
                    # ✨ មុខងារពិសេសបំផុត៖ កាត់តបញ្ចូលសំឡេងខ្មែរទៅក្នុងវីដេអូដើម
                    st.write("🎬 កំពុងដកសំឡេងអង់គ្លេងចេញ និងបញ្ជ្រាបសំឡេងខ្មែរចូលទៅក្នុងវីដេអូ (Merge Video)...")
                    video_clip = VideoFileClip(video_path)
                    audio_clip = AudioFileClip(full_audio_path)
                    
                    # កំណត់សំឡេងខ្មែរចូលទៅក្នុងវីដេអូ
                    final_clip = video_clip.set_audio(audio_clip)
                    output_video_path = "output_khmer_video.mp4"
                    
                    # ផលិតចេញជាហ្វាយវីដេអូផ្លូវការ
                    final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
                    
                    # បិទការប្រើប្រាស់ហ្វាយដើម្បីកុំឱ្យជាប់គាំង memory
                    video_clip.close()
                    audio_clip.close()
                    final_clip.close()
                    
                    st.session_state['output_video'] = output_video_path
                    status.update(label="ផលិតវីដេអូជោគជ័យ!", state="complete", expanded=False)
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"កំហុសបច្គេកទេស៖ {e}")
        
        # បង្ហាញផ្ទាំងវីដេអូភាសាខ្មែរដែលផលិតរួចសម្រាប់ឱ្យទាញយក (Download)
        if 'output_video' in st.session_state and os.path.exists(st.session_state['output_video']):
            st.markdown("---")
            st.subheader("🎉 វីដេអូជាភាសាខ្មែរដែលផលិតរួចរាល់")
            st.video(st.session_state['output_video'])
            
            with open(st.session_state['output_video'], "rb") as f:
                st.download_button(
                    label="📥 ទាញយកវីដេអូភាសាខ្មែរពេញលេញ (.mp4)",
                    data=f,
                    file_name="khmer_dubbed_video.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

    with col_sub:
        st.subheader("🎙️ Dubbing Studio Control")

        if 'dubbing_data' in st.session_state:
            for index, item in enumerate(st.session_state['dubbing_data']):
                audio_path = f"audio_chunks/voice_{index}.mp3"
                gender_detected = item.get("speaker_gender", "Male")
                
                with st.container():
                    st.markdown(f"""
                    <div class="dub-container">
                        <span style="color: #1565C0; font-weight: bold;">⏱️ {item['start_time']} - {item['end_time']}</span> 
                        <span class="speaker-tag">👤 តួអង្គ៖ {gender_detected}</span><br>
                        <small style="color: gray;">🇺🇸 {item['english_text']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    new_khmer_text = st.text_input("កែសម្រួលអត្ថបទខ្មែរ៖", value=item['khmer_text'], key=f"input_{index}")
                    default_voice_idx = 1 if gender_detected.lower() == "female" else 0
                    chosen_voice = st.selectbox("ជ្រើសរើសសំឡេង៖", ["ប្រុស (Piseth)", "ស្រី (Sreyrath)"], index=default_voice_idx, key=f"voice_select_{index}")
                    
                    if new_khmer_text != item['khmer_text']:
                        st.session_state['dubbing_data'][index]['khmer_text'] = new_khmer_text
                        with st.spinner("កំពុងធ្វើបច្ចុប្បន្នភាពសំឡេង..."):
                            asyncio.run(generate_single_audio_v3(new_khmer_text, chosen_voice, speed_string, audio_path))
                        st.rerun()
                    
                    if os.path.exists(audio_path):
                        st.audio(audio_path, format="audio/mp3")
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("សូមចុចប៊ូតុងខាងឆ្វេង ដើម្បីឱ្យ AI ចាប់ផ្ដើមផលិតវីដេអូ និងបំបែកអត្ថបទ។")
