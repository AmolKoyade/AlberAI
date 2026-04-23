import streamlit as st
from config import setup_client
from image_handler import handle_image_generation
from chat_handler import handle_text_chat

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Albert", page_icon="🤖", layout="wide")

# --- 2. MOBILE FIX: Disable Pull to Refresh ---
st.markdown("""
    <style>
        * { overscroll-behavior-y: none !important; }
        html, body { overscroll-behavior-y: none !important; }
        .main, .block-container { overscroll-behavior-y: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SECURE API LOADING ---
client = setup_client()

# --- 4. UI SETUP ---
st.title("🤖 I am Albert")
st.caption("2026 Edition: Vision • Research • Unstoppable Art")

with st.sidebar:
    st.header("Settings & Files")
    uploaded_file = st.file_uploader("Upload Image/PDF/Doc", type=["pdf", "docx", "jpg", "jpeg", "png"])
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Render chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], str) and msg["content"].startswith("__IMAGE__"):
            image_url = msg["content"].replace("__IMAGE__", "")
            st.markdown(
                f'<img src="{image_url}" width="100%" style="border-radius: 12px;" />',
                unsafe_allow_html=True
            )
        else:
            st.markdown(msg["content"])


# ---------------------------------------------------------------------------
# AI-BASED INTENT DETECTOR
# ---------------------------------------------------------------------------
def is_image_request(prompt: str, client) -> bool:
    """
    Instead of checking for trigger keywords (which misses many cases and
    causes false positives), we ask the LLM itself to decide — exactly like
    ChatGPT, Gemini, and Groq do.

    The model returns a single word: IMAGE or TEXT.
    We use a tiny, fast model call (no streaming needed).
    """
    classifier_prompt = f"""You are an intent classifier. 
A user sent this message: "{prompt}"

Does the user want you to GENERATE / CREATE / DRAW / SHOW an image or photo?
Reply with exactly one word — either IMAGE or TEXT. Nothing else.

Examples:
"a dog playing in the snow" → IMAGE
"what does a black hole look like" → IMAGE  
"show me a sunset over the ocean" → IMAGE
"portrait of a woman in Renaissance style" → IMAGE
"neon city at night" → IMAGE
"who invented the telephone" → TEXT
"explain quantum physics" → TEXT
"what is the capital of France" → TEXT
"write me a poem about the moon" → TEXT
"summarize this document" → TEXT
"""
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": classifier_prompt}],
            temperature=0,
            max_tokens=5   # We only need one word: IMAGE or TEXT
        )
        answer = resp.choices[0].message.content.strip().upper()
        return answer == "IMAGE"
    except Exception:
        # If classifier fails, fall back to a basic keyword check as safety net
        fallback_triggers = ["draw", "generate image", "create image", "paint",
                             "show me a picture", "make an image", "design"]
        return any(t in prompt.lower() for t in fallback_triggers)


# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("Ask me anything, or describe an image to create..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Use AI to decide intent — not keywords
        if is_image_request(prompt, client):
            # --- PATH A: IMAGE GENERATION ---
            full_response = handle_image_generation(prompt, client)
        else:
            # --- PATH B: TEXT / VISION / RESEARCH ---
            full_response = handle_text_chat(prompt, client, uploaded_file, st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": full_response})