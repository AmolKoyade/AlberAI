import streamlit as st
from utils import extract_text, encode_image, get_web_context

# ---------------------------------------------------------------------------
# HOW HISTORY WORKS
# ---------------------------------------------------------------------------
# st.session_state.messages  → stores EVERY message, never trimmed.
#                               This is what the UI renders — full chat history.
#
# clean_history (below)      → only the last API_CONTEXT_LIMIT clean messages
#                               sent to Groq per request. This prevents token
#                               overflow on Groq's free tier (~6000 tokens/req).
#
# These are TWO separate things. The user sees everything. The API gets a
# rolling window. This is exactly how ChatGPT and Gemini handle long chats.
# ---------------------------------------------------------------------------

API_CONTEXT_LIMIT = 10   # How many past messages to send to Groq per request


def handle_text_chat(prompt, client, uploaded_file, messages):
    file_txt, is_img, b64_img = "", False, None

    # --- File processing ---
    if uploaded_file is not None:
        if uploaded_file.type.startswith("image"):
            is_img = True
            b64_img = encode_image(uploaded_file)
        else:
            file_txt = extract_text(uploaded_file)

    with st.status("🔍 Researching...", expanded=False):
        web_info = get_web_context(prompt)

    # ---------------------------------------------------------------------------
    # Build API history — rolling window of last API_CONTEXT_LIMIT messages.
    # Rules:
    #   1. Skip __IMAGE__ entries (they are URLs, not text — crash the API)
    #   2. Skip any message whose content is not a plain string (e.g. list
    #      from a previous vision turn — also crashes the API)
    #   3. Exclude the current user message (messages[-1]) — we append it below
    #   4. Take only the last API_CONTEXT_LIMIT messages from what remains
    #
    # NOTE: This does NOT affect st.session_state.messages — the full chat
    # history is always stored and displayed. This only affects what Groq sees.
    # ---------------------------------------------------------------------------
    api_history = [
        {"role": m["role"], "content": m["content"]}
        for m in messages[:-1]                          # exclude current message
        if isinstance(m["content"], str)                # must be plain string
        and not m["content"].startswith("__IMAGE__")    # skip image history entries
    ][-API_CONTEXT_LIMIT:]                              # rolling window for API

    # --- Append the current user message to the API payload ---
    if is_img and b64_img:
        # Groq base64 image format (NOT OpenAI's image_url format)
        api_history.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"Web context: {web_info}\n\nQuestion: {prompt}"},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64_img
                    }
                }
            ]
        })
        model = "meta-llama/llama-4-scout-17b-16e-instruct"
    else:
        user_message = f"Question: {prompt}"
        if file_txt:
            user_message = f"File content:\n{file_txt}\n\n{user_message}"
        if web_info:
            user_message = f"Web context:\n{web_info}\n\n{user_message}"
        api_history.append({"role": "user", "content": user_message})
        model = "llama-3.3-70b-versatile"

    # --- Stream the response ---
    resp_placeholder = st.empty()
    full_response = "Sorry, I ran into an issue. Please try again."

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=api_history,
            stream=True,
            max_tokens=2048
        )
        full_response = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta
                resp_placeholder.markdown(full_response + "▌")
        resp_placeholder.markdown(full_response)

    except Exception as e:
        resp_placeholder.markdown(full_response)
        st.error(f"Error: {str(e)}")

    return full_response