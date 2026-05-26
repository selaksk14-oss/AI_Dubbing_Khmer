import streamlit as st
import google.generativeai as genai
import json, re, asyncio, os, shutil, time, tempfile, subprocess, requests
import nest_asyncio

nest_asyncio.apply()

# ──────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────
st.set_page_config(
    page_title="KhmerDub",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

TMP       = tempfile.gettempdir()
AUDIO_DIR = os.path.join(TMP, "kd_audio")
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
]
EDGE_VOICES = {
    "🧑 Piseth (បុរស)":  "km-KH-PisethNeural",
    "👩 Sreymom (ស្ត្រី)": "km-KH-SreymomNeural",
}

# ──────────────────────────────────────────
#  STYLES
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:       #0a0e1a;
  --surface:  #111827;
  --border:   #1f2d45;
  --accent:   #3b82f6;
  --accent2:  #8b5cf6;
  --success:  #10b981;
  --warn:     #f59e0b;
  --danger:   #ef4444;
  --text:     #e2e8f0;
  --muted:    #64748b;
  --radius:   12px;
}

html, body, [class*="css"] {
  font-family: 'Sora', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
.main { background: var(--bg) !important; }
.block-container { padding: 2rem 2.5rem 3rem !important; max-width: 1400px; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Inputs */
input, textarea, [data-baseweb="select"] {
  background: #0d1526 !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: 'Sora', sans-serif !important;
}
input:focus, textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,.15) !important;
}

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius) !important;
  font-family: 'Sora', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
  padding: 0.65rem 1.4rem !important;
  transition: opacity .2s, transform .15s !important;
  width: 100% !important;
}
.stButton > button:hover { opacity: .88 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-radius: 10px !important;
  padding: 4px !important;
  gap: 4px !important;
  border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 7px !important;
  color: var(--muted) !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  padding: 0.45rem 1rem !important;
}
.stTabs [aria-selected="true"] {
  background: var(--accent) !important;
  color: #fff !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
  background: #0d1526 !important;
  border: 2px dashed var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }

/* Progress */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
  border-radius: 4px !important;
}

/* Status */
[data-testid="stStatusWidget"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

/* Radio */
[data-testid="stRadio"] label { color: var(--text) !important; }

/* Selectbox */
[data-baseweb="select"] > div { background: #0d1526 !important; border-color: var(--border) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* Hide default branding */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
#  UI HELPERS
# ──────────────────────────────────────────
def card(content, color="var(--border)"):
    st.markdown(f"""
    <div style="background:var(--surface);border:1px solid {color};
    border-radius:var(--radius);padding:1.1rem 1.3rem;margin-bottom:.75rem;">
    {content}</div>""", unsafe_allow_html=True)

def badge(text, color):
    colors = {
        "green":  ("#10b98122","#10b981"),
        "blue":   ("#3b82f622","#3b82f6"),
        "red":    ("#ef444422","#ef4444"),
        "yellow": ("#f59e0b22","#f59e0b"),
        "purple": ("#8b5cf622","#8b5cf6"),
    }
    bg, fg = colors.get(color, ("#ffffff22","#ffffff"))
    return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:600;">{text}</span>'

def metric_row(items):
    cols_html = "".join([
        f"""<div style="flex:1;background:var(--surface);border:1px solid var(--border);
        border-radius:10px;padding:1rem;text-align:center;">
        <div style="font-size:1.8rem;font-weight:700;color:var(--text);line-height:1">{v}</div>
        <div style="font-size:.65rem;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:1px">{k}</div>
        </div>""" for k, v in items
    ])
    st.markdown(f'<div style="display:flex;gap:10px;margin-bottom:1rem;">{cols_html}</div>',
                unsafe_allow_html=True)

def section(title):
    st.markdown(f"""
    <div style="font-size:.8rem;font-weight:700;color:var(--muted);
    text-transform:uppercase;letter-spacing:2px;margin-bottom:.75rem;
    padding-bottom:.5rem;border-bottom:1px solid var(--border);">
    {title}</div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────
#  GEMINI AUTO-DETECT
# ──────────────────────────────────────────
def get_gemini_model(api_key: str) -> str:
    genai.configure(api_key=api_key)
    for name in GEMINI_MODELS:
        try:
            genai.GenerativeModel(name).generate_content("hi")
            return name
        except Exception:
            continue
    raise RuntimeError("គ្មាន Gemini model ណាដែល available ទេ។ សូម check API key ឬ enable Gemini API.")

# ──────────────────────────────────────────
#  SECRET HELPER
# ──────────────────────────────────────────
def get_secret(k):
    try: return st.secrets.get(k, "")
    except: return ""

# ──────────────────────────────────────────
#  JSON PARSE
# ──────────────────────────────────────────
def safe_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    try: return json.loads(text)
    except: pass
    m = re.search(r"(\[.*\])", text, re.DOTALL)
    if m:
        try: return json.loads(m.group(1))
        except: pass
    raise ValueError("AI មិន return JSON ត្រឹមត្រូវ — សូម try ម្ដងទៀត។")

# ──────────────────────────────────────────
#  FFMPEG HELPERS
# ──────────────────────────────────────────
def ffmpeg_ok():
    return shutil.which("ffmpeg") is not None

def get_dur(path):
    try:
        r = subprocess.run(
            ["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1",path],
            capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except: return None

def ts2sec(ts):
    ts = ts.replace(",",".").strip()
    p  = ts.split(":")
    try: return float(p[0])*3600+float(p[1])*60+float(p[2])
    except: return 0.0

def speed_seg(inp, out, target, maxspeed=1.5):
    dur = get_dur(inp)
    if not dur or dur<=0: shutil.copy(inp,out); return
    ratio = min(max(dur/target, 0.5), maxspeed)
    if abs(ratio-1.0)<0.05: shutil.copy(inp,out); return
    subprocess.run(["ffmpeg","-y","-i",inp,"-filter:a",f"atempo={ratio:.4f}",out],
                   capture_output=True, timeout=60)

def build_audio_track(data, total_dur):
    synced = os.path.join(TMP,"kd_synced"); os.makedirs(synced,exist_ok=True)
    parts=[]
    for i,seg in enumerate(data):
        start=ts2sec(seg["start_time"]); end=ts2sec(seg["end_time"])
        slot=max(end-start,0.1)
        raw=os.path.join(AUDIO_DIR,f"seg_{i}.mp3")
        adj=os.path.join(synced,f"adj_{i}.mp3")
        if os.path.exists(raw):
            speed_seg(raw,adj,slot)
            parts.append({"start":start,"path":adj,"dur":get_dur(adj) or slot})
        else:
            parts.append({"start":start,"path":None,"dur":0})

    silence=os.path.join(TMP,"kd_silence.mp3")
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"anullsrc=r=44100:cl=stereo",
                    "-t",str(total_dur+2),silence], capture_output=True, timeout=60)

    inputs=["-i",silence]
    fparts=["[0:a]aformat=sample_rates=44100:channel_layouts=stereo[base]"]
    valid=[]; idx=1
    for p in parts:
        if p["path"] and os.path.exists(p["path"]):
            dm=int(p["start"]*1000)
            inputs+=["-i",p["path"]]
            fparts.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={dm}|{dm}[a{idx}]")
            valid.append(f"[a{idx}]"); idx+=1

    if not valid: return silence
    all_in="[base]"+"".join(valid)
    fparts.append(f"{all_in}amix=inputs={1+len(valid)}:duration=first:dropout_transition=0[out]")
    out=os.path.join(TMP,"kd_full.mp3")
    subprocess.run(["ffmpeg","-y"]+inputs+["-filter_complex",";".join(fparts),
                    "-map","[out]","-c:a","mp3","-q:a","2",out],
                   capture_output=True, timeout=300)
    return out

def mux(vpath, apath, opath):
    r=subprocess.run(["ffmpeg","-y","-i",vpath,"-i",apath,
                      "-map","0:v:0","-map","1:a:0","-shortest",
                      "-c:v","copy","-c:a","aac",opath],
                     capture_output=True, text=True, timeout=300)
    if r.returncode!=0: raise RuntimeError(r.stderr[-500:])

def extract_audio(vpath, opath, dur=60):
    subprocess.run(["ffmpeg","-y","-i",vpath,"-t",str(dur),
                    "-vn","-acodec","mp3","-q:a","2",opath],
                   capture_output=True, timeout=120)

# ──────────────────────────────────────────
#  TTS HELPERS
# ──────────────────────────────────────────
import edge_tts

async def _tts_one(text, voice, rate, path):
    try: await edge_tts.Communicate(text, voice, rate=rate).save(path)
    except: pass

async def tts_all(data, voice, rate):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    await asyncio.gather(*[
        _tts_one(seg["khmer_text"], voice, rate,
                 os.path.join(AUDIO_DIR, f"seg_{i}.mp3"))
        for i,seg in enumerate(data)
    ])

def el_tts(text, voice_id, key, path):
    r=requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={"xi-api-key":key,"Content-Type":"application/json"},
                    json={"text":text,"model_id":"eleven_multilingual_v2",
                          "voice_settings":{"stability":.5,"similarity_boost":.75}},
                    timeout=60)
    if r.status_code!=200: raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
    open(path,"wb").write(r.content)

def el_clone(sample, name, key):
    with open(sample,"rb") as f:
        r=requests.post("https://api.elevenlabs.io/v1/voices/add",
                        headers={"xi-api-key":key},
                        data={"name":name,"description":"KhmerDub"},
                        files={"files":(os.path.basename(sample),f,"audio/mpeg")},
                        timeout=120)
    if r.status_code!=200: raise RuntimeError(f"Clone {r.status_code}: {r.text[:300]}")
    return r.json()["voice_id"]

def el_tts_all(data, voice_id, key):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    for i,seg in enumerate(data):
        try: el_tts(seg["khmer_text"], voice_id, key, os.path.join(AUDIO_DIR,f"seg_{i}.mp3"))
        except Exception as e: st.warning(f"⚠️ Segment {i+1}: {e}")

# ──────────────────────────────────────────
#  SRT
# ──────────────────────────────────────────
def build_srt(data, lang="khmer"):
    key = "khmer_text" if lang=="khmer" else "english_text"
    out=[]
    for i,seg in enumerate(data,1):
        def fix(t):
            t=t.strip()
            if "," not in t and "." not in t: t+=",000"
            return t.replace(".",",")
        out.append(f"{i}\n{fix(seg['start_time'])} --> {fix(seg['end_time'])}\n{seg.get(key,'')}\n")
    return "\n".join(out)

def apath(i): return os.path.join(AUDIO_DIR, f"seg_{i}.mp3")

# ──────────────────────────────────────────
#  SIDEBAR
# ──────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding:1.2rem 0 .5rem;">
      <div style="font-size:1.5rem;font-weight:700;letter-spacing:-1px;">
        🎙️ KhmerDub
      </div>
      <div style="font-size:.75rem;color:var(--muted);margin-top:2px;">
        AI Video Dubbing · v3.0
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Gemini Key ──
    section("🔑 Gemini API Key")
    gemini_key = st.text_input("gemini", value=get_secret("GEMINI_API_KEY"),
                                placeholder="AIza…", type="password",
                                label_visibility="collapsed")
    if gemini_key:
        st.markdown(badge("✓ Connected","green"), unsafe_allow_html=True)
    else:
        st.markdown(badge("⚠ Key needed","yellow"), unsafe_allow_html=True)
        st.caption("👉 [Get free key](https://aistudio.google.com)")

    st.divider()

    # ── Voice Mode ──
    section("🎙️ Voice Engine")
    voice_mode = st.radio("vm", ["Edge TTS (ឥតគិតថ្លៃ)", "ElevenLabs (Clone)"],
                          label_visibility="collapsed")

    if voice_mode.startswith("Edge"):
        voice_lbl  = st.selectbox("Voice", list(EDGE_VOICES.keys()))
        edge_voice = EDGE_VOICES[voice_lbl]
        el_key     = None
        speed_map  = {"យឺត":"-20%","ធម្មតា":"+0%","លឿន":"+15%","លឿនខ្លាំង":"+30%"}
        speed_lbl  = st.select_slider("ល្បឿន", list(speed_map.keys()), value="ធម្មតា")
        tts_rate   = speed_map[speed_lbl]
    else:
        edge_voice = None
        tts_rate   = "+0%"
        section("ElevenLabs Key")
        el_key = st.text_input("el", value=get_secret("ELEVENLABS_API_KEY"),
                                placeholder="sk_…", type="password",
                                label_visibility="collapsed")
        if el_key:
            st.markdown(badge("✓ Connected","purple"), unsafe_allow_html=True)
        st.caption("👉 [Get free key](https://elevenlabs.io)")

    st.divider()

    # ── System status ──
    section("⚙️ System")
    ffok = ffmpeg_ok()
    st.markdown(
        badge("✓ FFmpeg Ready","green") if ffok else badge("✗ FFmpeg Missing","red"),
        unsafe_allow_html=True
    )
    if not ffok:
        st.caption("Video merge unavailable — audio only")

# ──────────────────────────────────────────
#  HEADER
# ──────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1.5rem;">
  <h1 style="font-size:2rem;font-weight:700;letter-spacing:-1.5px;
  background:linear-gradient(135deg,#3b82f6,#8b5cf6);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:4px;">KhmerDub AI</h1>
  <p style="color:var(--muted);font-size:.9rem;margin:0;">
  Upload វីដេអូ · AI បកប្រែ · TTS ខ្មែរ · Export MP4
  </p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
#  TABS
# ──────────────────────────────────────────
t1, t2, t3 = st.tabs(["🚀 Dub","🎛 Studio","📝 SRT"])

# ══════════════════════════════════════════
#  TAB 1 — DUB
# ══════════════════════════════════════════
with t1:
    L, R = st.columns([3, 2], gap="large")

    with L:
        section("📤 Upload វីដេអូ")
        up = st.file_uploader("vid", type=["mp4","mov","mkv","avi"],
                               label_visibility="collapsed")
        if up:
            if st.session_state.get("vname") != up.name:
                st.session_state.update({
                    "vname": up.name, "vbytes": up.read(),
                    "data": None, "done": False,
                    "cloned_id": None, "audio_out": None, "vid_out": None
                })
                if os.path.exists(AUDIO_DIR): shutil.rmtree(AUDIO_DIR)
            st.video(st.session_state["vbytes"])

    with R:
        section("⚙️ Controls")
        if not up:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
            border-radius:var(--radius);padding:1.4rem;line-height:2;">
            <b style="color:var(--accent)">របៀបប្រើ</b><br>
            <span style="color:var(--muted);font-size:.85rem;">
            ① Upload វីដេអូ MP4/MOV<br>
            ② ដាក់ Gemini API Key នៅ Sidebar<br>
            ③ ជ្រើស Voice Engine<br>
            ④ ចុច <b style="color:var(--text)">Start Dubbing</b><br>
            ⑤ Download MP4 ខ្មែរ 🎉
            </span></div>""", unsafe_allow_html=True)
        else:
            vb   = st.session_state["vbytes"]
            segs = len(st.session_state.get("data") or [])
            sz   = len(vb)/1e6
            metric_row([
                ("MB", f"{sz:.1f}"),
                ("Segments", segs),
                ("Status", "✓" if st.session_state.get("done") else "—"),
            ])

            # Validate before showing button
            if not gemini_key:
                st.warning("⚠️ ត្រូវការ Gemini API Key")
            elif voice_mode.startswith("ElevenLabs") and not el_key:
                st.warning("⚠️ ត្រូវការ ElevenLabs API Key")
            else:
                label = "🔄 Re-Dub" if st.session_state.get("done") else "🚀 Start Dubbing"
                if st.button(label, use_container_width=True):
                    st.session_state.update({
                        "data": None, "done": False,
                        "cloned_id": None, "audio_out": None, "vid_out": None
                    })
                    if os.path.exists(AUDIO_DIR): shutil.rmtree(AUDIO_DIR)

                    with st.status("⚡ Processing…", expanded=True) as status:
                        try:
                            # Save video
                            with tempfile.NamedTemporaryFile(delete=False,suffix=".mp4") as tf:
                                tf.write(vb); vtmp=tf.name

                            # Step 1 — Upload to Gemini
                            st.write("📤 **Step 1/5** — Uploading video to Gemini…")
                            genai.configure(api_key=gemini_key)
                            gfile = genai.upload_file(path=vtmp)
                            st.write("⏳ **Step 1/5** — Processing…")
                            t0=time.time()
                            while gfile.state.name=="PROCESSING":
                                if time.time()-t0>300: raise Exception("Gemini processing timeout (5min).")
                                time.sleep(4)
                                gfile=genai.get_file(gfile.name)
                            if gfile.state.name=="FAILED":
                                raise Exception("Google failed to process video. Try smaller/shorter file.")

                            # Step 2 — Translate
                            st.write("🤖 **Step 2/5** — Detecting model & translating…")
                            mname = get_gemini_model(gemini_key)
                            st.write(f"   ✓ Using **{mname}**")
                            model = genai.GenerativeModel(
                                mname,
                                generation_config={"response_mime_type":"application/json"}
                            )
                            prompt = """
Listen to ALL dialogue in this video. Translate every spoken line into natural, fluent Khmer for professional dubbing.

Return ONLY a JSON array, no extra text:
[{"start_time":"HH:MM:SS,mmm","end_time":"HH:MM:SS,mmm","english_text":"...","khmer_text":"..."}]

Rules:
- Capture every spoken word
- Natural Khmer for dubbing (not literal translation)
- Polite register unless speech is casual
- Preserve emotion and intent
- Precise timing
"""
                            resp  = model.generate_content([gfile, prompt])
                            data  = safe_json(resp.text)
                            if not isinstance(data,list) or not data:
                                raise ValueError("AI returned empty data. Try again.")
                            st.session_state["data"] = data
                            st.write(f"✅ **Step 2/5** — Got **{len(data)} segments**")

                            # Step 3 — TTS
                            if voice_mode.startswith("ElevenLabs"):
                                st.write("🎤 **Step 3/5** — Extracting voice for cloning…")
                                sp=os.path.join(TMP,"kd_sample.mp3")
                                extract_audio(vtmp,sp,60)
                                st.write("🔬 **Step 3/5** — Cloning voice (ElevenLabs)…")
                                vid=el_clone(sp,f"KhmerDub_{int(time.time())}",el_key)
                                st.session_state["cloned_id"]=vid
                                st.write("🎙️ **Step 4/5** — Generating Khmer audio…")
                                el_tts_all(data,vid,el_key)
                            else:
                                st.write(f"🎙️ **Step 3/5** — Generating {len(data)} audio segments…")
                                asyncio.run(tts_all(data, edge_voice, tts_rate))
                                st.write("✅ **Step 3/5** — Audio generated")

                            # Step 4 — Sync
                            st.write("⚙️ **Step 4/5** — Syncing audio to video timing…")
                            vdur = get_dur(vtmp) or 60.0
                            aout = build_audio_track(data, vdur)
                            st.session_state["audio_out"] = aout

                            # Step 5 — Merge
                            if ffok:
                                st.write("🎬 **Step 5/5** — Merging into final video…")
                                vout=os.path.join(TMP,"kd_final.mp4")
                                mux(vtmp,aout,vout)
                                st.session_state["vid_out"]=vout
                            else:
                                st.warning("⚠️ FFmpeg missing — audio only mode")

                            try: os.unlink(vtmp)
                            except: pass

                            st.session_state["done"]=True
                            status.update(label="✅ Done!", state="complete", expanded=False)
                            st.balloons()

                        except Exception as e:
                            status.update(label="❌ Error", state="error")
                            st.error(f"**Error:** {e}")
                            st.info("💡 **Tips:** ពិនិត្យ API key · វីដេអូ < 100MB · enable Gemini API")

            # Downloads
            if st.session_state.get("done"):
                st.divider()
                section("📥 Downloads")

                vout = st.session_state.get("vid_out")
                aout = st.session_state.get("audio_out")
                data = st.session_state.get("data",[])

                if vout and os.path.exists(vout):
                    with open(vout,"rb") as f:
                        st.download_button("🎬 Download Dubbed Video (.mp4)", f,
                                           "khmer_dubbed.mp4","video/mp4",
                                           use_container_width=True)
                    st.video(vout)
                elif aout and os.path.exists(aout):
                    with open(aout,"rb") as f:
                        st.download_button("🎵 Download Khmer Audio (.mp3)", f,
                                           "khmer_voiceover.mp3","audio/mp3",
                                           use_container_width=True)

                if data:
                    c1,c2=st.columns(2)
                    with c1:
                        st.download_button("📝 SRT ខ្មែរ",
                                           build_srt(data,"khmer").encode("utf-8"),
                                           "khmer.srt","text/plain",
                                           use_container_width=True)
                    with c2:
                        st.download_button("📝 SRT English",
                                           build_srt(data,"english").encode("utf-8"),
                                           "english.srt","text/plain",
                                           use_container_width=True)

# ══════════════════════════════════════════
#  TAB 2 — STUDIO
# ══════════════════════════════════════════
with t2:
    data = st.session_state.get("data")
    if not data:
        st.info("🚀 Run **Dub** tab first.")
    else:
        n     = len(data)
        ready = sum(1 for i in range(n) if os.path.exists(apath(i)))

        metric_row([
            ("Segments", n),
            ("Audio Ready", ready),
            ("Engine", voice_mode.split()[0]),
        ])

        c1,c2=st.columns([5,1])
        with c2:
            if st.button("🔄 Regen All"):
                with st.spinner("Regenerating all…"):
                    if voice_mode.startswith("Edge"):
                        asyncio.run(tts_all(data,edge_voice,tts_rate))
                    elif el_key and st.session_state.get("cloned_id"):
                        el_tts_all(data,st.session_state["cloned_id"],el_key)
                st.rerun()

        st.divider()
        for i,seg in enumerate(data):
            ap=apath(i)
            with st.container():
                st.markdown(f"""
                <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:10px;padding:.9rem 1rem;margin-bottom:.5rem;">
                <span style="background:#3b82f622;color:#3b82f6;padding:2px 8px;
                border-radius:12px;font-family:'JetBrains Mono',monospace;font-size:.72rem;">
                ⏱ {seg['start_time']} → {seg['end_time']}</span>
                <span style="float:right;color:var(--muted);font-size:.72rem;">#{i+1}</span>
                <div style="color:var(--muted);font-size:.8rem;font-style:italic;
                margin-top:.4rem;">🇺🇸 {seg.get('english_text','')}</div>
                </div>""", unsafe_allow_html=True)

                ct,cb=st.columns([5,1])
                with ct:
                    new_t=st.text_area(f"s{i}", value=seg["khmer_text"],
                                       key=f"kh_{i}", height=70,
                                       label_visibility="collapsed")
                with cb:
                    st.markdown("<div style='height:20px'></div>",unsafe_allow_html=True)
                    if st.button("▶",key=f"r{i}",help="Regenerate"):
                        st.session_state["data"][i]["khmer_text"]=new_t
                        try:
                            if voice_mode.startswith("Edge"):
                                asyncio.run(_tts_one(new_t,edge_voice,tts_rate,ap))
                            elif el_key and st.session_state.get("cloned_id"):
                                el_tts(new_t,st.session_state["cloned_id"],el_key,ap)
                        except Exception as e:
                            st.error(str(e))
                        st.rerun()

                if os.path.exists(ap):
                    st.audio(ap, format="audio/mp3")
                else:
                    st.markdown(badge("✗ No audio","red"),unsafe_allow_html=True)
                st.markdown("<div style='height:2px'></div>",unsafe_allow_html=True)

        st.divider()
        if st.button("🎬 Re-export Video (after edits)", use_container_width=True):
            if "vbytes" not in st.session_state:
                st.error("Video not found — re-upload in Dub tab.")
            elif not ffok:
                st.error("FFmpeg not available.")
            else:
                with st.spinner("Re-syncing…"):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False,suffix=".mp4") as tf:
                            tf.write(st.session_state["vbytes"]); vp=tf.name
                        vdur=get_dur(vp) or 60.0
                        aout=build_audio_track(st.session_state["data"],vdur)
                        vout=os.path.join(TMP,"kd_edited.mp4")
                        mux(vp,aout,vout)
                        try: os.unlink(vp)
                        except: pass
                        st.session_state["vid_out"]=vout
                        st.success("✅ Done! Download from **Dub** tab.")
                    except Exception as e:
                        st.error(str(e))

# ══════════════════════════════════════════
#  TAB 3 — SRT
# ══════════════════════════════════════════
with t3:
    data=st.session_state.get("data")
    if not data:
        st.info("🚀 Run **Dub** tab first.")
    else:
        sk,se=st.tabs(["🇰🇭 Khmer","🇺🇸 English"])
        with sk:
            srt=build_srt(data,"khmer")
            st.markdown(f"""<div style="background:var(--surface);border:1px solid var(--border);
            border-radius:10px;padding:1rem;font-family:'JetBrains Mono',monospace;
            font-size:.8rem;color:#94a3b8;max-height:360px;overflow-y:auto;
            white-space:pre-wrap;line-height:1.9;">{srt}</div>""",unsafe_allow_html=True)
            st.download_button("📥 Download Khmer SRT",srt.encode("utf-8"),
                               "khmer.srt","text/plain",use_container_width=True)
        with se:
            srt=build_srt(data,"english")
            st.markdown(f"""<div style="background:var(--surface);border:1px solid var(--border);
            border-radius:10px;padding:1rem;font-family:'JetBrains Mono',monospace;
            font-size:.8rem;color:#94a3b8;max-height:360px;overflow-y:auto;
            white-space:pre-wrap;line-height:1.9;">{srt}</div>""",unsafe_allow_html=True)
            st.download_button("📥 Download English SRT",srt.encode("utf-8"),
                               "english.srt","text/plain",use_container_width=True)

# ──────────────────────────────────────────
#  FOOTER
# ──────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;
color:var(--muted);font-size:.75rem;letter-spacing:.5px;">
KhmerDub v3.0 &nbsp;·&nbsp; Gemini AI &nbsp;·&nbsp; Edge TTS &nbsp;·&nbsp; ElevenLabs &nbsp;·&nbsp; FFmpeg
</div>""", unsafe_allow_html=True)
