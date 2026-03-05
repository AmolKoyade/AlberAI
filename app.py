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
st.set_page_config(page_title="Albert", page_icon="🤖", layout="centered")

# --- 2. SECURE API LOADING ---
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
    client = groq.Groq(api_key=API_KEY)
except Exception:
    st.error("⚠️ Developer Setup Required: Add 'GROQ_API_KEY' to Streamlit Secrets.")
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

# --- 4. ALBERT UI ---
st.title("🤖 I am Albert")
st.caption("Vision • Research • Memory • Enhanced AI Art")

with st.sidebar:
    st.header("📁 Upload Files")
    uploaded_file = st.file_uploader("Upload Image, PDF, or Doc", type=["pdf", "docx", "jpg", "jpeg", "png"])
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("Ask Albert to draw, analyze, or research..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # --- PATH A: IMAGE GENERATION (Wait-and-Verify Logic) ---
        image_keywords = ["draw", "generate", "image", "paint", "create a picture", "make a photo"]
        if any(word in prompt.lower() for word in image_keywords):
            with st.spinner("🎨 Albert is painting (this takes about 5-10 seconds)..."):
                # 1. AI Prompt Enhancement
                enhance_instruction = f"Expand this into a detailed 4k AI art prompt: '{prompt}'. Respond ONLY with the prompt."
                try:
                    enhanced_resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": enhance_instruction}]
                    )
                    art_prompt = enhanced_resp.choices[0].message.content
                except:
                    art_prompt = prompt

                # 2. Prepare URL
                encoded_art = urllib.parse.quote(art_prompt.strip())
                seed = random.randint(1, 1000000)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_art}?width=1024&height=1024&nologo=true&seed={seed}"
                
                # 3. Wait-and-Verify Fix
                image_ready = False
                for attempt in range(6): # Try for 12 seconds total
                    check = requests.get(image_url)
                    if check.status_code == 200 and len(check.content) > 5000: # Ensure it's not a tiny error icon
                        image_ready = True
                        break
                    time.sleep(2)

                if image_ready:
                    st.image(image_url, caption="Albert's Masterpiece")
                    st.markdown(f"[📥 Download this Image]({image_url})")
                    full_response = f"I've finished the painting! Here is the prompt I used: *{art_prompt}*"
                else:
                    st.error("The artist is busy! Please try sending the prompt again.")
                    full_response = "I had trouble rendering the image. Please try again!"

        # --- PATH B: TEXT & VISION ---
        else:
            file_context, is_image, base64_image = "", False, None
            if uploaded_file:
                if uploaded_file.type.startswith("image"):
                    is_image, base64_image = True, encode_image(uploaded_file)
                else:
                    file_context = extract_text(uploaded_file)

            with st.status("🔍 Researching...", expanded=False):
                web_info = get_web_context(prompt)
            
            messages_to_send = []
            for m in st.session_state.messages[:-1]:
                messages_to_send.append({"role": m["role"], "content": m["content"]})
            
            if is_image:
                messages_to_send.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Context: {web_info}\n\nQuestion: {prompt}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                })
            else:
                messages_to_send.append({"role": "user", "content": f"File: {file_context}\nWeb: {web_info}\nQ: {prompt}"})

            response_placeholder = st.empty()
            full_response = ""
            try:
                model = "meta-llama/llama-4-scout-17b-16e-instruct" if is_image else "llama-3.3-70b-versatile"
                stream = client.chat.completions.create(model=model, messages=messages_to_send, stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"Albert error: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})