import streamlit as st
import groq
import base64
import io
import urllib.parse
import random
import requests
import time
from PIL import Image
from duckduckgo_search import DDGS
from PyPDF2 import PdfReader
import docx

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Albert", page_icon="🤖", layout="wide")

# --- 2. SECURE API LOADING ---
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
    client = groq.Groq(api_key=API_KEY)
except Exception:
    st.error("⚠️ Setup Error: Add your 'GROQ_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 3. UTILITY FUNCTIONS ---
def extract_text(uploaded_file):
    text = ""
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            text += page.extract_text()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
    return text

def encode_image(uploaded_file):
    img = Image.open(uploaded_file)
    img.thumbnail((1024, 1024))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def get_web_context(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=2)]
            return "\n".join(results)
    except:
        return ""

# --- 4. UI SETUP ---
st.title("🤖 Albert: Your 2026 AI Assistant")
st.markdown("---")

with st.sidebar:
    st.header("Settings & Files")
    uploaded_file = st.file_uploader("Upload Image/PDF/Doc", type=["pdf", "docx", "jpg", "jpeg", "png"])
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("Draw me a futuristic car... or ask a question"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # --- PATH A: IMAGE GENERATION (RELIABLE 2026 LOGIC) ---
        img_triggers = ["draw", "generate", "image", "paint", "picture", "create"]
        if any(word in prompt.lower() for word in img_triggers):
            status_box = st.status("🎨 Albert is creating art...", expanded=True)
            
            # 1. Expand Prompt using Llama
            enhance_cmd = f"Rewrite this as a high-detail 4k AI art prompt: '{prompt}'. Focus on lighting/style. No preamble, just the prompt."
            try:
                enh_resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": enhance_cmd}])
                art_prompt = enh_resp.choices[0].message.content
            except:
                art_prompt = prompt

            # 2. Build Unified URL
            clean_art = urllib.parse.quote(art_prompt.strip())
            seed = random.randint(1, 999999)
            # gen.pollinations.ai is the stable 2026 endpoint
            image_url = f"https://gen.pollinations.ai/prompt/{clean_art}?width=1024&height=1024&nologo=true&seed={seed}&cache={time.time()}"
            
            # 3. Validation Loop
            image_ready = False
            for i in range(10): # Try for 20 seconds
                status_box.update(label=f"🖌️ Painting... (Attempt {i+1}/10)", state="running")
                try:
                    r = requests.get(image_url, timeout=10)
                    if r.status_code == 200 and len(r.content) > 10000: # 10kb check ensures it's a real image
                        image_ready = True
                        break
                except:
                    pass
                time.sleep(2)

            if image_ready:
                status_box.update(label="✅ Masterpiece Complete!", state="complete")
                st.image(image_url, caption=f"Albert's creation for: {prompt}")
                st.markdown(f"**[💾 Download High-Res]({image_url})**")
                full_response = f"I've generated that image! Prompt used: *{art_prompt}*"
            else:
                status_box.update(label="❌ Artist's Block (Server Timeout)", state="error")
                st.error("The art server didn't respond in time. Please try a simpler prompt.")
                full_response = "Sorry, I couldn't render that image right now."

        # --- PATH B: TEXT / VISION ---
        else:
            file_txt, is_img, b64_img = "", False, None
            if uploaded_file:
                if uploaded_file.type.startswith("image"):
                    is_img, b64_img = True, encode_image(uploaded_file)
                else:
                    file_txt = extract_text(uploaded_file)

            with st.status("🔍 Researching...", expanded=False):
                web_info = get_web_context(prompt)
            
            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
            
            if is_img:
                history.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Web Info: {web_info}\n\nQuestion: {prompt}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                })
                model = "meta-llama/llama-4-scout-17b-16e-instruct"
            else:
                history.append({"role": "user", "content": f"File: {file_txt}\nWeb: {web_info}\nQ: {prompt}"})
                model = "llama-3.3-70b-versatile"

            resp_placeholder = st.empty()
            full_response = ""
            try:
                stream = client.chat.completions.create(model=model, messages=history, stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        resp_placeholder.markdown(full_response + "▌")
                resp_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})