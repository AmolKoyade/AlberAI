import streamlit as st
import urllib.parse


def handle_image_generation(prompt, client):
    status_box = st.status("🎨 Albert is creating art...", expanded=True)

    # Step 1: Enhance prompt with Groq
    enhance_cmd = (
        f"Rewrite as a vivid 4k art prompt for exactly this subject: '{prompt}'. "
        f"Style: cinematic, photorealistic. UNDER 20 WORDS. "
        f"Only the prompt, no preamble, no extra text."
    )
    try:
        enh_resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": enhance_cmd}]
        )
        art_prompt = enh_resp.choices[0].message.content.strip()
    except Exception:
        art_prompt = prompt

    # Step 2: Build Pollinations URL
    # FIX: Removed random seed so same prompt = consistent image
    # FIX: Added enhance=false so Pollinations doesn't alter the prompt randomly
    encoded_prompt = urllib.parse.quote(art_prompt, safe="")
    image_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=1024&height=1024&nologo=true&enhance=false&model=flux"
    )

    # Step 3: Render image in browser via <img> tag
    status_box.update(label="✅ Sending to your browser...", state="complete")

    st.markdown(
        f"""
        <img src="{image_url}" 
             width="100%" 
             style="border-radius: 12px; margin-top: 8px;"
             alt="Generated image: {art_prompt}" />
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"📝 **Prompt:** *{art_prompt}*")
    st.markdown(f"**[💾 Download High-Res]({image_url})**")

    # FIX: Save image URL to history so it reappears on scroll
    full_response = f"__IMAGE__{image_url}"
    return full_response
