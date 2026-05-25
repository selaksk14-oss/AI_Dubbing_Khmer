import streamlit as st
import google.generativeai as genai
import json
import asyncio
import nest_asyncio
import edge_tts
import os
import shutil
import time
import tempfile
import subprocess
import requests

nest_asyncio.apply()

# ═══════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════
st.set_page_config(
    page_title="KhmerDub – AI Dubbing",
    layout="wide",
    page_icon="🎙️",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════
#  CSS
# ═══════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background: #f7f8fc;
    color: #1a1a2e;
}
.main { background: #f7f8fc; }
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e8eaf0;
}

/* Buttons */
.stButton > button {
    background: #1a1a2e;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 500;
    padding: 10px 20px;
    width: 100%;
    transition: background 0.2s;
}
.stButton > button:hover { background: #2d2d50; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox > div > div, .stRadio {
    background: #ffffff !important;
    border: 1.5px solid #e0e2ea !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    color: #1a1a2e !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #4f6ef7 !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,0.10) !important;
}

/* Cards */
.card {
    background: #fff;
    border: 1.5px solid #e8eaf0;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 12px;
}
.seg-card {
    background: #fff;
    border: 1.5px solid #e8eaf0;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.seg-time {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #4f6ef7;
    background: #eef1fe;
    padding: 2px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 6px;
}
.seg-eng {
    font-size: 0.82rem;
    color: #8890b0;
    font-style: italic;
    margin-bottom: 6px;
}

/* Metric strip */
.metric-strip { display: flex; gap: 10px; margin-bottom: 18px; }
.metric-box {
    flex: 1;
    background: #fff;
    border: 1.5px solid #e8eaf0;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
}
.metric-val { font-size: 1.6rem; font-weight: 600; color: #1a1a2e; line-height: 1; }
.metric-lbl { font-size: 0.68rem; color: #9098b8; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.8px; }

/* Pills */
.pill { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 500; }
.pill-green { background: #e8faf2; color: #22c55e; }
.pill-blue  { background: #eef1fe; color: #4f6ef7; }
.pill-red   { background: #fef2f2; color: #ef4444; }
.pill-yellow{ background: #fffbeb; color: #f59e0b; }

/* Section header */
.sec-hdr {
    font-size: 0.95rem; font-weight: 600; color: #1a1a2e;
    margin-bottom: 12px; padding-bottom: 8px;
    border-bottom: 2px solid #e8eaf0;
}

/* Info / Warn boxes */
.info-box {
    background: #f0f4ff; border: 1.5px solid #c5caf5;
    border-radius: 10px; padding: 14px 16px;
    font-size: 0.85rem; color: #3a4880; line-height: 1.7;
}
.warn-box {
    background: #fffbeb; border: 1.5px solid #fcd34d;
    border-radius: 10px; padding: 14px 16px;
    font-size: 0.85rem; color: #92400e; line-height: 1.7;
}
.success-box {
    background: #e8faf2; border: 1.5px solid #86efac;
    border-radius: 10px; padding: 14px 16px;
    font-size: 0.85rem; color: #166534; line-height: 1.7;
}

/* Steps */
.step-row { display: flex; gap: 8px; align-items: flex-start; margin-bottom: 10px; }
.step-num {
    background: #1a1a2e; color: #fff;
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.78rem; font-weight: 600; flex-shrink: 0;
}
.step-txt { font-size: 0.88rem; color: #3a3a5e; padding-top: 3px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #eef0f8;
    border-radius: 10px; padding: 4px; border: none;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px; color: #6068a0;
    font-weight: 500; font-size: 0.88rem;
}
.stTabs [aria-selected="true"] {
    background: #fff !important; color: #1a1a2e !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

/* SRT */
.srt-box {
    background: #fff; border: 1.5px solid #e8eaf0;
    border-radius: 10px; padding: 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem; color: #4a5080;
    max-height: 320px; overflow-y: auto;
    line-height: 1.9; white-space: pre-wrap;
}

/* Progress */
.stProgress > div > div > div { background: #4f6ef7; border-radius: 4px; }

/* Hide branding */
#MainMenu, footer { visibility: hidden; }
hr { border: none; border-top: 1.5px solid #e8eaf0; margin: 18px 0; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════
TMP = tempfile.gettempdir()
AUDIO_DIR = os.path.join(TMP, "kd_chunks")
EDGE_VOICES = {
    "Piseth (បុរស — Microsoft)": "km-KH-PisethNeural",
    "Sreymom (ស្ត្រី — Microsoft)": "km-KH-SreymomNeural",
}

# ═══════════════════════════════════════
#  HELPERS — TTS
# ═══════════════════════════════════════
async def _edge_one(text, voice, rate, path):
    await edge_tts.Communicate(text, voice, rate=rate).save(path)

async def edge_tts_all(data, voice, rate):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    await asyncio.gather(*[
        _edge_one(item["khmer_text"], voice, rate,
                  os.path.join(AUDIO_DIR, f"seg_{i}.mp3"))
        for i, item in enumerate(data)
    ])

async def edge_tts_one(text, voice, rate, path):
    await _edge_one(text, voice, rate, path)

def elevenlabs_tts(text, voice_id, api_key, path):
    """ElevenLabs TTS — single segment."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    r = requests.post(url, json=body, headers=headers, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
    with open(path, "wb") as f:
        f.write(r.content)

def elevenlabs_clone_voice(sample_path, name, api_key):
    """Upload voice sample → return voice_id."""
    url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {"xi-api-key": api_key}
    with open(sample_path, "rb") as f:
        files = {"files": (os.path.basename(sample_path), f, "audio/mpeg")}
        data = {"name": name, "description": "KhmerDub cloned voice"}
        r = requests.post(url, headers=headers, data=data, files=files, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Clone error {r.status_code}: {r.text[:300]}")
    return r.json()["voice_id"]

def elevenlabs_tts_all(data, voice_id, api_key):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    for i, item in enumerate(data):
        p = os.path.join(AUDIO_DIR, f"seg_{i}.mp3")
        elevenlabs_tts(item["khmer_text"], voice_id, api_key, p)

def get_elevenlabs_voices(api_key):
    r = requests.get("https://api.elevenlabs.io/v1/voices",
                     headers={"xi-api-key": api_key}, timeout=20)
    if r.status_code != 200:
        return {}
    voices = r.json().get("voices", [])
    return {v["name"]: v["voice_id"] for v in voices}

# ═══════════════════════════════════════
#  HELPERS — FFmpeg
# ═══════════════════════════════════════
def ffmpeg_ok():
    return shutil.which("ffmpeg") is not None

def get_duration(path):
    """Return duration in seconds via ffprobe."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return None

def ts_to_sec(ts):
    """HH:MM:SS,mmm or HH:MM:SS → float seconds."""
    ts = ts.replace(",", ".").strip()
    parts = ts.split(":")
    try:
        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s
    except Exception:
        return 0.0

def speed_adjust_segment(in_path, out_path, target_dur, max_speed=1.5):
    """Speed-up audio to fit target_dur. Max speed = max_speed."""
    src_dur = get_duration(in_path)
    if src_dur is None or src_dur <= 0:
        shutil.copy(in_path, out_path)
        return
    ratio = src_dur / target_dur
    ratio = min(ratio, max_speed)   # cap at max_speed
    ratio = max(ratio, 0.5)         # don't slow down below 0.5x
    if abs(ratio - 1.0) < 0.05:
        shutil.copy(in_path, out_path)
        return
    subprocess.run(
        ["ffmpeg", "-y", "-i", in_path,
         "-filter:a", f"atempo={ratio:.4f}", out_path],
        capture_output=True
    )

def build_synced_audio(data, total_video_dur):
    """
    Build one long audio track with silence padding,
    each segment speed-adjusted to fit its slot.
    Returns path to final WAV.
    """
    parts = []
    synced_dir = os.path.join(TMP, "kd_synced")
    os.makedirs(synced_dir, exist_ok=True)

    for i, seg in enumerate(data):
        start = ts_to_sec(seg["start_time"])
        end   = ts_to_sec(seg["end_time"])
        slot  = max(end - start, 0.1)

        raw   = os.path.join(AUDIO_DIR, f"seg_{i}.mp3")
        adj   = os.path.join(synced_dir, f"adj_{i}.mp3")

        if os.path.exists(raw):
            speed_adjust_segment(raw, adj, slot)
            adj_dur = get_duration(adj) or slot
        else:
            adj = None
            adj_dur = 0

        parts.append({
            "start": start,
            "path": adj,
            "dur": adj_dur,
        })

    # Build concat using ffmpeg concat filter with adelay
    # Strategy: create silence base + overlay each segment
    silence_path = os.path.join(TMP, "kd_silence.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"anullsrc=r=44100:cl=stereo",
         "-t", str(total_video_dur + 2),
         silence_path],
        capture_output=True
    )

    # Build filter_complex for amix
    inputs = ["-i", silence_path]
    filter_parts = ["[0:a]aformat=sample_rates=44100:channel_layouts=stereo[base]"]
    mix_inputs = "[base]"
    valid_parts = []

    idx = 1
    for p in parts:
        if p["path"] and os.path.exists(p["path"]):
            delay_ms = int(p["start"] * 1000)
            inputs += ["-i", p["path"]]
            filter_parts.append(
                f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                f"adelay={delay_ms}|{delay_ms}[a{idx}]"
            )
            valid_parts.append(f"[a{idx}]")
            idx += 1

    if not valid_parts:
        return silence_path

    all_inputs = mix_inputs + "".join(valid_parts)
    n_streams = 1 + len(valid_parts)
    filter_parts.append(
        f"{all_inputs}amix=inputs={n_streams}:duration=first:dropout_transition=0[out]"
    )

    filter_complex = ";".join(filter_parts)
    out_path = os.path.join(TMP, "kd_synced_full.mp3")
    subprocess.run(
        ["ffmpeg", "-y"] + inputs +
        ["-filter_complex", filter_complex,
         "-map", "[out]", "-c:a", "mp3", "-q:a", "2", out_path],
        capture_output=True
    )
    return out_path

def mux_video(video_path, audio_path_full, output_path):
    r = subprocess.run(
        ["ffmpeg", "-y",
         "-i", video_path,
         "-i", audio_path_full,
         "-map", "0:v:0", "-map", "1:a:0",
         "-shortest", "-c:v", "copy", "-c:a", "aac",
         output_path],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])

def extract_audio_from_video(video_path, out_path, duration=60):
    """Extract first `duration` seconds of audio for voice cloning."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path,
         "-t", str(duration),
         "-vn", "-acodec", "mp3", "-q:a", "2", out_path],
        capture_output=True
    )

def get_video_duration(video_path):
    return get_duration(video_path) or 60.0

# ═══════════════════════════════════════
#  HELPERS — SRT
# ═══════════════════════════════════════
def build_srt(data, lang="khmer"):
    key = "khmer_text" if lang == "khmer" else "english_text"
    lines = []
    for i, seg in enumerate(data, 1):
        def fix(t):
            t = t.strip()
            if "," not in t and "." not in t:
                t += ",000"
            return t.replace(".", ",")
        lines.append(f"{i}\n{fix(seg['start_time'])} --> {fix(seg['end_time'])}\n{seg.get(key,'')}\n")
    return "\n".join(lines)

def audio_path(i):
    return os.path.join(AUDIO_DIR, f"seg_{i}.mp3")

# ═══════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎙️ KhmerDub")
    st.caption("AI Video Dubbing Studio")
    st.markdown("---")

    st.markdown("**🔑 Gemini API Key**")
    gemini_key = st.text_input("", placeholder="AIza…", type="password",
                                key="gemini_key", label_visibility="collapsed")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        st.markdown('<span class="pill pill-green">✓ Gemini Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill pill-yellow">⚠ Key needed</span>', unsafe_allow_html=True)
        st.caption("[Get free key →](https://aistudio.google.com)")

    st.markdown("---")
    st.markdown("**🎙️ Voice Mode**")
    voice_mode = st.radio(
        "", ["Edge TTS (ឥតគិតថ្លៃ)", "ElevenLabs Clone (API Key)"],
        label_visibility="collapsed"
    )

    if voice_mode == "Edge TTS (ឥតគិតថ្លៃ)":
        voice_lbl = st.selectbox("Voice", list(EDGE_VOICES.keys()))
        edge_voice = EDGE_VOICES[voice_lbl]
        el_key = None
    else:
        st.markdown("**ElevenLabs API Key**")
        el_key = st.text_input("", placeholder="sk_…", type="password",
                                key="el_key", label_visibility="collapsed")
        st.caption("[Get free key →](https://elevenlabs.io)")
        if el_key:
            st.markdown('<span class="pill pill-green">✓ ElevenLabs Connected</span>', unsafe_allow_html=True)
        edge_voice = None

    st.markdown("---")
    st.markdown("**⚡ Speed (Edge TTS)**")
    speed_map = {"យឺត –20%": "-20%", "ធម្មតា": "+0%", "លឿន +15%": "+15%", "លឿនខ្លាំង +30%": "+30%"}
    speed_lbl = st.selectbox("", list(speed_map.keys()), index=1, label_visibility="collapsed")
    tts_rate = speed_map[speed_lbl]

    st.markdown("---")
    st.caption("v2.1 · Gemini 2.5 Flash · Edge TTS · ElevenLabs")

# ═══════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════
st.markdown("## 🎙️ KhmerDub — AI Video Dubbing")
st.markdown('<p style="color:#6068a0;margin-top:-12px;margin-bottom:20px;">Upload វីដេអូ → AI បកប្រែ → បង្កើតសំឡេង → Download MP4 ខ្មែរ</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════
#  TABS
# ═══════════════════════════════════════
tab_main, tab_studio, tab_srt = st.tabs([
    "🚀  One-Click Dub",
    "🎛️  Dubbing Studio",
    "📝  SRT Subtitle",
])

# ═══════════════════════════════════════
#  TAB 1 — ONE-CLICK DUB
# ═══════════════════════════════════════
with tab_main:
    col_left, col_right = st.columns([1.4, 1], gap="large")

    with col_left:
        st.markdown('<div class="sec-hdr">📤 Upload វីដេអូ</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "MP4 / MOV / MKV / AVI",
            type=["mp4", "mov", "mkv", "avi"],
            label_visibility="visible"
        )

        if uploaded:
            if st.session_state.get("video_name") != uploaded.name:
                st.session_state["video_name"]  = uploaded.name
                st.session_state["video_bytes"] = uploaded.read()
                for k in ["dubbing_data", "done", "cloned_voice_id",
                          "full_audio", "dubbed_video"]:
                    st.session_state.pop(k, None)
                if os.path.exists(AUDIO_DIR):
                    shutil.rmtree(AUDIO_DIR)
            st.video(st.session_state["video_bytes"])

    with col_right:
        st.markdown('<div class="sec-hdr">⚙️ Controls</div>', unsafe_allow_html=True)

        if not uploaded:
            st.markdown("""
            <div class="info-box">
            <b>របៀបប្រើ:</b><br><br>
            <div class="step-row"><div class="step-num">1</div><div class="step-txt">Upload វីដេអូ MP4</div></div>
            <div class="step-row"><div class="step-num">2</div><div class="step-txt">បញ្ចូល API Keys នៅ Sidebar</div></div>
            <div class="step-row"><div class="step-num">3</div><div class="step-txt">ចុច <b>Start Dubbing</b></div></div>
            <div class="step-row"><div class="step-num">4</div><div class="step-txt">ទទួល MP4 ខ្មែរ + SRT</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            vb = st.session_state["video_bytes"]
            segs = len(st.session_state.get("dubbing_data", []))
            sz = len(vb) / 1_000_000

            st.markdown(f"""
            <div class="metric-strip">
                <div class="metric-box"><div class="metric-val">{sz:.1f}</div><div class="metric-lbl">MB</div></div>
                <div class="metric-box"><div class="metric-val">{segs}</div><div class="metric-lbl">Segments</div></div>
                <div class="metric-box"><div class="metric-val">{"✓" if st.session_state.get("done") else "—"}</div><div class="metric-lbl">Done</div></div>
            </div>
            """, unsafe_allow_html=True)

            if not gemini_key:
                st.warning("⚠️ សូមបញ្ចូល Gemini API Key នៅ Sidebar")
            elif voice_mode == "ElevenLabs Clone (API Key)" and not el_key:
                st.warning("⚠️ សូមបញ្ចូល ElevenLabs API Key នៅ Sidebar")
            else:
                btn = "🔄 Re-Dub" if st.session_state.get("done") else "🚀 Start Dubbing"
                if st.button(btn, use_container_width=True):
                    # Reset
                    for k in ["dubbing_data", "done", "cloned_voice_id",
                               "full_audio", "dubbed_video"]:
                        st.session_state.pop(k, None)
                    if os.path.exists(AUDIO_DIR):
                        shutil.rmtree(AUDIO_DIR)

                    with st.status("🔄 Processing…", expanded=True) as status:
                        try:
                            # ── Save video to temp ──
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
                                tf.write(vb); video_tmp = tf.name

                            # ── STEP 1: Gemini translate ──
                            st.write("📤 Step 1/5 — Uploading to Gemini…")
                            raw = genai.upload_file(path=video_tmp)
                            st.write("⏳ Waiting for Google to process…")
                            while raw.state.name == "PROCESSING":
                                time.sleep(5)
                                raw = genai.get_file(raw.name)
                            if raw.state.name == "FAILED":
                                raise Exception("Google could not process the video.")

                            st.write("🤖 Step 2/5 — AI translating to Khmer…")
                            model = genai.GenerativeModel(
                                "gemini-2.5-flash",
                                generation_config={"response_mime_type": "application/json"}
                            )
                            prompt = """
Listen carefully to ALL spoken dialogue in this video.
Translate every line into natural, fluent Khmer suitable for professional dubbing.

Return ONLY a valid JSON array — no markdown, no explanation:
[
  {
    "start_time": "HH:MM:SS,mmm",
    "end_time": "HH:MM:SS,mmm",
    "english_text": "original spoken words",
    "khmer_text": "ការបកប្រែជាភាសាខ្មែរ"
  }
]

Rules:
- Capture every spoken word accurately
- Khmer must sound natural when read aloud (dubbing style)
- Use polite Khmer unless speech is casual
- Preserve emotion and intent of original speaker
- Timing must match the video precisely
"""
                            resp = model.generate_content([raw, prompt])
                            data = json.loads(resp.text)
                            st.session_state["dubbing_data"] = data
                            st.write(f"✅ Got {len(data)} segments")

                            # ── STEP 2: Voice Clone (if ElevenLabs) ──
                            if voice_mode == "ElevenLabs Clone (API Key)":
                                st.write("🎤 Step 3/5 — Extracting voice from video for cloning…")
                                sample_path = os.path.join(TMP, "kd_voice_sample.mp3")
                                extract_audio_from_video(video_tmp, sample_path, duration=60)

                                st.write("🔬 Cloning voice with ElevenLabs…")
                                voice_id = elevenlabs_clone_voice(
                                    sample_path, f"KhmerDub_{int(time.time())}", el_key
                                )
                                st.session_state["cloned_voice_id"] = voice_id
                                st.write("✅ Voice cloned!")

                                st.write("🎙️ Step 4/5 — Generating Khmer audio (ElevenLabs)…")
                                elevenlabs_tts_all(data, voice_id, el_key)
                            else:
                                st.write(f"🎙️ Step 3/5 — Generating {len(data)} Khmer audio segments…")
                                asyncio.run(edge_tts_all(data, edge_voice, tts_rate))

                            # ── STEP 3: Sync + Merge ──
                            st.write("⚙️ Step 4/5 — Speed-adjusting & syncing to video timing…")
                            vid_dur = get_video_duration(video_tmp)
                            synced_audio = build_synced_audio(data, vid_dur)

                            if ffmpeg_ok():
                                st.write("🎬 Step 5/5 — Merging audio into video…")
                                dubbed_out = os.path.join(TMP, "kd_dubbed_final.mp4")
                                mux_video(video_tmp, synced_audio, dubbed_out)
                                st.session_state["dubbed_video"] = dubbed_out
                            else:
                                st.warning("⚠️ FFmpeg not found — skipping video merge. Download audio only.")
                                st.session_state["full_audio"] = synced_audio

                            os.unlink(video_tmp)
                            st.session_state["done"] = True
                            status.update(label="✅ Done!", state="complete", expanded=False)
                            st.balloons()

                        except Exception as e:
                            status.update(label="❌ Error", state="error")
                            st.error(str(e))

            # ── Download section ──
            if st.session_state.get("done"):
                st.markdown("---")
                st.markdown("### 📥 Downloads")

                # Dubbed Video
                if st.session_state.get("dubbed_video") and \
                   os.path.exists(st.session_state["dubbed_video"]):
                    with open(st.session_state["dubbed_video"], "rb") as f:
                        st.download_button(
                            "🎬 Download Dubbed Video (.mp4)",
                            data=f,
                            file_name="khmer_dubbed.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    st.video(st.session_state["dubbed_video"])

                # Full audio fallback
                elif st.session_state.get("full_audio") and \
                     os.path.exists(st.session_state["full_audio"]):
                    with open(st.session_state["full_audio"], "rb") as f:
                        st.download_button(
                            "🎵 Download Khmer Audio (.mp3)",
                            data=f,
                            file_name="khmer_voiceover.mp3",
                            mime="audio/mp3",
                            use_container_width=True
                        )

                # SRT downloads
                data = st.session_state.get("dubbing_data", [])
                if data:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button(
                            "📝 SRT ខ្មែរ",
                            build_srt(data, "khmer").encode("utf-8"),
                            "khmer.srt", "text/plain",
                            use_container_width=True
                        )
                    with c2:
                        st.download_button(
                            "📝 SRT English",
                            build_srt(data, "english").encode("utf-8"),
                            "english.srt", "text/plain",
                            use_container_width=True
                        )

# ═══════════════════════════════════════
#  TAB 2 — DUBBING STUDIO (Edit segments)
# ═══════════════════════════════════════
with tab_studio:
    data = st.session_state.get("dubbing_data")
    if not data:
        st.info("🚀 Run **One-Click Dub** first to see segments here.")
    else:
        n = len(data)
        ready = sum(1 for i in range(n) if os.path.exists(audio_path(i)))

        st.markdown(f"""
        <div class="metric-strip">
            <div class="metric-box"><div class="metric-val">{n}</div><div class="metric-lbl">Segments</div></div>
            <div class="metric-box"><div class="metric-val">{ready}</div><div class="metric-lbl">Audio</div></div>
            <div class="metric-box"><div class="metric-val">{voice_mode.split()[0]}</div><div class="metric-lbl">Mode</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Regen all
        col_ra, col_rb = st.columns([3, 1])
        with col_rb:
            if st.button("🔄 Regen All Audio"):
                with st.spinner("Regenerating…"):
                    if voice_mode == "Edge TTS (ឥតគិតថ្លៃ)":
                        asyncio.run(edge_tts_all(data, edge_voice, tts_rate))
                    elif el_key and st.session_state.get("cloned_voice_id"):
                        elevenlabs_tts_all(data, st.session_state["cloned_voice_id"], el_key)
                st.rerun()

        st.markdown("---")

        for i, seg in enumerate(data):
            ap = audio_path(i)
            st.markdown(f"""
            <div class="seg-card">
                <span class="seg-time">⏱ {seg['start_time']} → {seg['end_time']}</span>
                <span style="float:right;font-size:0.75rem;color:#b0b8d0;">#{i+1}</span>
                <div class="seg-eng">🇺🇸 {seg.get('english_text','')}</div>
            </div>
            """, unsafe_allow_html=True)

            col_t, col_b = st.columns([4, 1])
            with col_t:
                new_text = st.text_area(
                    f"#{i+1}", value=seg["khmer_text"],
                    key=f"kh_{i}", height=74,
                    label_visibility="collapsed"
                )
            with col_b:
                st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                if st.button("🔄", key=f"regen_{i}", help="Update audio"):
                    st.session_state["dubbing_data"][i]["khmer_text"] = new_text
                    with st.spinner(""):
                        if voice_mode == "Edge TTS (ឥតគិតថ្លៃ)":
                            asyncio.run(edge_tts_one(new_text, edge_voice, tts_rate, ap))
                        elif el_key and st.session_state.get("cloned_voice_id"):
                            elevenlabs_tts(new_text, st.session_state["cloned_voice_id"], el_key, ap)
                    st.rerun()

            if os.path.exists(ap):
                st.audio(ap, format="audio/mp3")
            else:
                st.markdown('<span class="pill pill-red">✕ No audio</span>', unsafe_allow_html=True)

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Re-export after edits
        st.markdown("---")
        if st.button("🎬 Re-export Dubbed Video (after edits)", use_container_width=True):
            if "video_bytes" not in st.session_state:
                st.error("Video not found. Re-upload in Tab 1.")
            elif not ffmpeg_ok():
                st.error("FFmpeg not available on this server.")
            else:
                with st.spinner("Re-syncing and merging…"):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
                            tf.write(st.session_state["video_bytes"]); vp = tf.name
                        vid_dur = get_video_duration(vp)
                        synced = build_synced_audio(
                            st.session_state["dubbing_data"], vid_dur
                        )
                        out = os.path.join(TMP, "kd_dubbed_edited.mp4")
                        mux_video(vp, synced, out)
                        os.unlink(vp)
                        st.session_state["dubbed_video"] = out
                        st.success("✅ Done! Go to Tab 1 to download.")
                    except Exception as e:
                        st.error(str(e))

# ═══════════════════════════════════════
#  TAB 3 — SRT
# ═══════════════════════════════════════
with tab_srt:
    data = st.session_state.get("dubbing_data")
    if not data:
        st.info("🚀 Run **One-Click Dub** first.")
    else:
        st.markdown('<div class="sec-hdr">📝 SRT Subtitle</div>', unsafe_allow_html=True)

        tk, te = st.tabs(["🇰🇭 Khmer", "🇺🇸 English"])

        with tk:
            srt_kh = build_srt(data, "khmer")
            st.markdown(f'<div class="srt-box">{srt_kh}</div>', unsafe_allow_html=True)
            st.download_button(
                "📥 Download Khmer SRT",
                srt_kh.encode("utf-8"),
                "khmer_subtitle.srt", "text/plain",
                use_container_width=True
            )

        with te:
            srt_en = build_srt(data, "english")
            st.markdown(f'<div class="srt-box">{srt_en}</div>', unsafe_allow_html=True)
            st.download_button(
                "📥 Download English SRT",
                srt_en.encode("utf-8"),
                "english_subtitle.srt", "text/plain",
                use_container_width=True
            )

# ═══════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════
st.markdown("---")
st.markdown('<p style="text-align:center;color:#b0b8d0;font-size:0.78rem;">KhmerDub v2.1 · Gemini 2.5 Flash · Edge TTS · ElevenLabs · FFmpeg</p>', unsafe_allow_html=True)
