import streamlit as st
import google.generativeai as genai
import json
import asyncio
import edge_tts
import os
import shutil
import time

# 1. រៀបចំទម្រង់វេបសាយ
st.set_page_config(page_title="AI Video Dubbing Studio", layout="wide", page_icon="🎬")

# បន្ថែម CSS ដើម្បីឱ្យមើលទៅស្អាតជាងមុន
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1E88E5; color: white; }
    .stAudio { width: 100%; }
    .dub-container { border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 5px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🎬 AI Video Dubbing & Khmer Translation</h1>", unsafe_allow_html=True)

# របារចំហៀង
st.sidebar.title("⚙️ កំណត់រចនាសម្ព័ន្ធ")
api_key = st.sidebar.text_input("🔑 Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.sidebar.warning("⚠️ សូមបញ្ចូល API Key ដើម្បីបន្ត")

# មុខងារជំនួយសម្រាប់បង្កើតសំឡេងច្រើនក្នុងពេលតែមួយ
async def generate_all_audio(dubbing_data):
    if not os.path.exists("audio_chunks"):
        os.makedirs("audio_chunks")
    
    tasks = []
    for index, item in enumerate(dubbing_data):
        output_path = f"audio_chunks/voice_{index}.mp3"
        voice = "km-KH-PisethNeural"
        communicate = edge_tts.Communicate(item['khmer_text'], voice, rate="+0%")
        tasks.append(communicate.save(output_path))
    
    await asyncio.gather(*tasks)

# មុខងារសម្រាប់បង្កើតសំឡេងឡើងវិញតែមួយឃ្លា
async def generate_single_audio(text, output_path):
    voice = "km-KH-PisethNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# 2. ផ្នែក Upload វីដេអូ
uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4)", type=["mp4"])

if uploaded_file and api_key:
    video_path = "input_video.mp4"
    
    if 'current_video' not in st.session_state or st.session_state['current_video'] != uploaded_file.name:
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())
        st.session_state['current_video'] = uploaded_file.name
        
        if 'dubbing_data' in st.session_state:
            del st.session_state['dubbing_data']

    col_video, col_sub = st.columns([1, 1.2])

    with col_video:
        st.subheader("📹 វីដេអូដើម")
        st.video(video_path)
        
        if st.button("🚀 ចាប់ផ្ដើមបកប្រែ និងបញ្ចូលសំឡេង"):
            if os.path.exists("audio_chunks"):
                shutil.rmtree("audio_chunks")
            
            with st.status("កំពុងដំណើរការ...", expanded=True) as status:
                try:
                    st.write("កំពុង Upload វីដេអូទៅ Gemini...")
                    raw_video = genai.upload_file(path=video_path)
                    
                    # ✨ បន្ថែម៖ មុខងាររង់ចាំឱ្យវីដេអូដំណើរការចប់ (ACTIVE) សិន ដើម្បីការពារការគាំង
                    st.write("⏳ កំពុងរង់ចាំ Google ដំណើរការហ្វាយវីដេអូ (អាចចំណាយពេលបន្តិច)...")
                    while raw_video.state.name == "PROCESSING":
                        time.sleep(5)
                        raw_video = genai.get_file(raw_video.name)
                    
                    if raw_video.state.name == "FAILED":
                        raise Exception("ការ Upload និងដំណើរការវីដេអូនៅលើ Server របស់ Google បានបរាជ័យ។")
                    
                    st.write("Gemini កំពុងវិភាគ និងបកប្រែអត្ថបទ...")
                    model = genai.GenerativeModel(
                        model_name="gemini-2.5-flash",
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    prompt = """
                    Watch this video, listen to the English audio, and translate it into natural Khmer.
                    The Khmer translation should be suitable for dubbing and voiceover.
                    Output strictly in this JSON array format:
                    [
                      {
                        "start_time": "HH:MM:SS",
                        "end_time": "HH:MM:SS",
                        "english_text": "English text",
                        "khmer_text": "ឃ្លាបកប្រែខ្មែរ"
                      }
                    ]
                    """
                    
                    response = model.generate_content([raw_video, prompt])
                    st.session_state['dubbing_data'] = json.loads(response.text)
                    
                    st.write("កំពុងបង្កើតសំឡេង AI ភាសាខ្មែរ...")
                    asyncio.run(generate_all_audio(st.session_state['dubbing_data']))
                    
                    status.update(label="រួចរាល់!", state="complete", expanded=False)
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"កំហុសបច្ចេកទេស៖ {e}")

    with col_sub:
        st.subheader("🎙️ Dubbing Studio")

        if 'dubbing_data' in st.session_state:
            for index, item in enumerate(st.session_state['dubbing_data']):
                audio_path = f"audio_chunks/voice_{index}.mp3"
                
                with st.container():
                    st.markdown(f"""
                    <div class="dub-container">
                        <span style="color: #1E88E5; font-weight: bold;">⏱️ {item['start_time']} - {item['end_time']}</span><br>
                        <small style="color: gray;">🇺🇸 {item['english_text']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    new_khmer_text = st.text_input(
                        "កែសម្រួលអត្ថបទខ្មែរ៖", 
                        value=item['khmer_text'], 
                        key=f"input_{index}"
                    )
                    
                    if new_khmer_text != item['khmer_text']:
                        st.session_state['dubbing_data'][index]['khmer_text'] = new_khmer_text
                        with st.spinner("កំពុងធ្វើបច្ចុប្បន្នភាពសំឡេង..."):
                            asyncio.run(generate_single_audio(new_khmer_text, audio_path))
                        st.rerun()
                    
                    if os.path.exists(audio_path):
                        st.audio(audio_path, format="audio/mp3")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
            st.markdown("---")
            if st.button("📦 រួមបញ្ចូលសំឡេងទាំងអស់ចូលគ្នា"):
                full_audio_path = "full_khmer_voiceover.mp3"
                with open(full_audio_path, "wb") as outfile:
                    for i in range(len(st.session_state['dubbing_data'])):
                        chunk_path = f"audio_chunks/voice_{i}.mp3"
                        if os.path.exists(chunk_path):
                            with open(chunk_path, "rb") as infile:
                                outfile.write(infile.read())
                
                st.success("🎉 រួមបញ្ចូលសំឡេងបានជោគជ័យ!")
                with open(full_audio_path, "rb") as f:
                    st.download_button(
                        label="📥 ទាញយកហ្វាយសំឡេងពេញលេញ (.mp3)",
                        data=f,
                        file_name="full_khmer_voiceover.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
        else:
            st.info("សូមចុចប៊ូតុងខាងលើ ដើម្បីចាប់ផ្ដើមបង្ហាញលទ្ធផលនៅទីនេះ។")

# បន្ថែម Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>អភិវឌ្ឍន៍ដោយប្រើប្រាស់ Gemini 2.5 Flash & Edge TTS</p>", unsafe_allow_html=True)