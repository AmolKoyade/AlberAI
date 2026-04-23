import streamlit as st
from config import setup_client
from image_handler import handle_image_generation
from chat_handler import handle_text_chat

st.set_page_config(
    page_title="Aura AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ── CORE PALETTE ── */
:root {
    --bg:        #1A2B1E;
    --bg2:       #213325;
    --bg3:       #273D2C;
    --gold:      #C9A96E;
    --gold2:     #E2C97E;
    --gold3:     #8C6E3F;
    --goldfade:  rgba(201,169,110,0.10);
    --goldbrd:   rgba(201,169,110,0.20);
    --goldbrd2:  rgba(201,169,110,0.38);
    --muted:     rgba(201,169,110,0.50);
}

/* ── GLOBAL RESET ── */
* { overscroll-behavior-y: none !important; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background-color: var(--bg) !important;
    color: var(--gold) !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
}

/* ── MAIN CONTAINER ── */
[data-testid="stMain"],
[data-testid="block-container"],
.block-container {
    background-color: var(--bg) !important;
    padding-top: 1.2rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background-color: var(--bg2) !important;
    border-right: 1px solid var(--goldbrd) !important;
    min-width: 220px !important;
    max-width: 260px !important;
}
[data-testid="stSidebar"] * {
    color: var(--gold) !important;
}
[data-testid="stSidebar"] .stButton button {
    width: 100%;
    background: var(--goldfade) !important;
    color: var(--gold2) !important;
    border: 1px solid var(--goldbrd2) !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    padding: 8px 0 !important;
    font-weight: 500 !important;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(201,169,110,0.18) !important;
}

/* ── SIDEBAR FILE UPLOADER ── */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: var(--bg3) !important;
    border: 1px dashed var(--goldbrd2) !important;
    border-radius: 10px !important;
    padding: 10px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: var(--bg3) !important;
    border: none !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
    color: var(--muted) !important;
    font-size: 12px !important;
}

/* ── HEADER / TITLE ── */
h1, h2, h3, .stTitle {
    color: var(--gold2) !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
}
[data-testid="stCaptionContainer"] p,
.stCaption { color: var(--muted) !important; font-size: 12px !important; }

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    background: var(--bg3) !important;
    border: 1px solid var(--goldbrd) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    margin-bottom: 8px !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background: var(--goldfade) !important;
    border-color: var(--goldbrd2) !important;
    margin-left: 10% !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: var(--gold2) !important;
    font-size: 14px !important;
    line-height: 1.65 !important;
}

/* ── CHAT AVATAR ── */
[data-testid="stChatMessageAvatarUser"] {
    background: var(--gold3) !important;
    border: 1px solid var(--goldbrd2) !important;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background: var(--bg2) !important;
    border: 1px solid var(--goldbrd2) !important;
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] {
    background: var(--bg2) !important;
    border-top: 1px solid var(--goldbrd) !important;
    padding: 10px 16px !important;
}
[data-testid="stChatInputTextArea"],
[data-testid="stChatInput"] textarea {
    background: var(--bg3) !important;
    color: var(--gold2) !important;
    border: 1px solid var(--goldbrd2) !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    caret-color: var(--gold2) !important;
    padding: 10px 14px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--muted) !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--gold3) !important;
    box-shadow: 0 0 0 2px rgba(201,169,110,0.15) !important;
}
[data-testid="stChatInputSubmitButton"] button {
    background: var(--goldfade) !important;
    border: 1px solid var(--goldbrd2) !important;
    border-radius: 8px !important;
    color: var(--gold2) !important;
}
[data-testid="stChatInputSubmitButton"] button:hover {
    background: rgba(201,169,110,0.22) !important;
}
[data-testid="stChatInputSubmitButton"] svg path {
    fill: var(--gold2) !important;
}

/* ── STATUS BOX (web search / generating) ── */
[data-testid="stStatus"],
[data-testid="stStatusContainer"] {
    background: var(--bg2) !important;
    border: 1px solid var(--goldbrd) !important;
    border-radius: 10px !important;
    color: var(--gold) !important;
}
[data-testid="stStatus"] * { color: var(--gold) !important; }

/* ── ALERTS & ERRORS ── */
[data-testid="stAlert"] {
    background: rgba(201,169,110,0.08) !important;
    border: 1px solid var(--goldbrd2) !important;
    border-radius: 10px !important;
    color: var(--gold2) !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg2); }
::-webkit-scrollbar-thumb { background: var(--gold3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }

/* ── MARKDOWN INSIDE CHAT ── */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
    color: var(--gold2) !important;
}
[data-testid="stMarkdownContainer"] code {
    background: var(--bg3) !important;
    color: var(--gold2) !important;
    border: 1px solid var(--goldbrd) !important;
    border-radius: 4px !important;
    padding: 1px 6px !important;
}
[data-testid="stMarkdownContainer"] pre {
    background: var(--bg3) !important;
    border: 1px solid var(--goldbrd) !important;
    border-radius: 8px !important;
}
[data-testid="stMarkdownContainer"] a {
    color: var(--gold) !important;
    text-decoration: underline;
    text-underline-offset: 3px;
}

/* ── IMAGES (generated art) ── */
[data-testid="stImage"] img {
    border-radius: 12px !important;
    border: 1px solid var(--goldbrd2) !important;
}

/* ── DOWNLOAD BUTTON ── */
[data-testid="stDownloadButton"] button {
    background: var(--goldfade) !important;
    color: var(--gold2) !important;
    border: 1px solid var(--goldbrd2) !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(201,169,110,0.20) !important;
}

/* ── DIVIDER ── */
hr { border-color: var(--goldbrd) !important; }

/* ── SOURCE CARD (sidebar) ── */
.source-card {
    background: var(--bg3);
    border: 1px solid var(--goldbrd);
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 8px;
}
.source-card-title {
    font-size: 12px;
    font-weight: 500;
    color: var(--gold2);
    margin-bottom: 2px;
}
.source-card-sub {
    font-size: 11px;
    color: var(--muted);
}
.source-tag {
    display: inline-block;
    margin-top: 5px;
    background: var(--goldfade);
    border: 1px solid var(--goldbrd);
    border-radius: 4px;
    padding: 1px 7px;
    font-size: 10px;
    color: var(--gold);
}

/* ── TOP NAV LABEL ── */
.aura-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0 16px;
    border-bottom: 1px solid var(--goldbrd);
    margin-bottom: 16px;
}
.aura-logo-mark {
    width: 34px; height: 34px;
    background: var(--goldfade);
    border: 1px solid var(--goldbrd2);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; color: var(--gold2);
    font-weight: 500;
}
.aura-logo-text {
    font-size: 17px;
    font-weight: 500;
    color: var(--gold2);
    letter-spacing: 0.04em;
}
.aura-logo-sub {
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.nav-section-label {
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 6px 0 4px;
}
.nav-link {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 7px;
    font-size: 13px;
    color: var(--gold);
    margin-bottom: 2px;
    cursor: pointer;
}
.nav-link.active {
    background: var(--goldfade);
    color: var(--gold2);
    border: 1px solid var(--goldbrd);
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--goldfade);
    border: 1px solid var(--goldbrd);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    color: var(--gold);
    margin-bottom: 12px;
}
.status-dot {
    width: 6px; height: 6px;
    background: #4ade80;
    border-radius: 50%;
}
</style>
""", unsafe_allow_html=True)

client = setup_client()

with st.sidebar:
    st.markdown("""
    <div class="aura-header">
        <div class="aura-logo-mark">✦</div>
        <div>
            <div class="aura-logo-text">Aura AI</div>
            <div class="aura-logo-sub">Intelligence Suite</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="nav-section-label">Navigation</div>
    <div class="nav-link active">⬡ &nbsp; Chat</div>
    <div class="nav-link">◫ &nbsp; Library</div>
    <div class="nav-link">◈ &nbsp; Sources</div>
    <div class="nav-link">◉ &nbsp; Dashboard</div>
    <div class="nav-link">⊙ &nbsp; Settings</div>
    <br/>
    <div class="nav-section-label">Upload Source</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload Image / PDF / Doc",
        type=["pdf", "docx", "jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        st.markdown(f"""
        <div class="source-card">
            <div class="source-card-title">{uploaded_file.name}</div>
            <div class="source-card-sub">Ready for analysis</div>
            <div class="source-tag">{uploaded_file.type.split('/')[-1].upper()}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="nav-section-label">Session</div>', unsafe_allow_html=True)

    if st.button("⟳  Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
    <div>
        <span style="font-size:22px; font-weight:500; color:#E2C97E; letter-spacing:0.03em;">✦ Aura AI</span>
        <span style="font-size:12px; color:rgba(201,169,110,0.5); margin-left:10px;">2026 Edition · Vision · Research · Art</span>
    </div>
    <div class="status-badge"><div class="status-dot"></div> Online</div>
</div>
<hr style="margin-bottom:16px;"/>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding:48px 20px 32px;">
        <div style="font-size:40px; margin-bottom:12px; color:#C9A96E;">✦</div>
        <div style="font-size:20px; font-weight:500; color:#E2C97E; margin-bottom:8px;">How can I assist you today?</div>
        <div style="font-size:13px; color:rgba(201,169,110,0.55); margin-bottom:32px;">
            Ask me anything, upload a document, or describe an image to create
        </div>
        <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
            <div style="background:rgba(201,169,110,0.08); border:1px solid rgba(201,169,110,0.22); border-radius:10px; padding:10px 16px; font-size:12px; color:#C9A96E; cursor:pointer;">
                ◈ &nbsp; Summarise a document
            </div>
            <div style="background:rgba(201,169,110,0.08); border:1px solid rgba(201,169,110,0.22); border-radius:10px; padding:10px 16px; font-size:12px; color:#C9A96E; cursor:pointer;">
                ◉ &nbsp; Research a topic
            </div>
            <div style="background:rgba(201,169,110,0.08); border:1px solid rgba(201,169,110,0.22); border-radius:10px; padding:10px 16px; font-size:12px; color:#C9A96E; cursor:pointer;">
                ✦ &nbsp; Generate artwork
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], str) and msg["content"].startswith("__IMAGE__"):
            image_url = msg["content"].replace("__IMAGE__", "")
            st.markdown(
                f'<img src="{image_url}" width="100%" style="border-radius:12px; border:1px solid rgba(201,169,110,0.30);" />',
                unsafe_allow_html=True
            )
        else:
            st.markdown(msg["content"])


def is_image_request(prompt: str, client) -> bool:
    classifier_prompt = f"""You are an intent classifier.
A user sent this message: "{prompt}"

Does the user want you to GENERATE / CREATE / DRAW / SHOW an image or artwork?
Reply with exactly one word — either IMAGE or TEXT. Nothing else.

Examples:
"a dog playing in snow" → IMAGE
"neon city at night" → IMAGE
"portrait of a woman" → IMAGE
"draw me a sunset" → IMAGE
"generate a dragon" → IMAGE
"explain quantum physics" → TEXT
"who invented the phone" → TEXT
"create a business plan" → TEXT
"write me a poem" → TEXT
"""
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": classifier_prompt}],
            temperature=0,
            max_tokens=5
        )
        return resp.choices[0].message.content.strip().upper() == "IMAGE"
    except Exception:
        fallback = ["draw", "generate image", "create image", "paint",
                    "make an image", "show me a picture"]
        return any(t in prompt.lower() for t in fallback)


if prompt := st.chat_input("Ask Aura AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if is_image_request(prompt, client):
            full_response = handle_image_generation(prompt, client)
        else:
            full_response = handle_text_chat(
                prompt, client, uploaded_file, st.session_state.messages
            )

    st.session_state.messages.append({"role": "assistant", "content": full_response})