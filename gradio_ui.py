# gradio_ui.py
"""
Polished Gradio Web UI for Interdimensional Radio

Features
--------
1. Character selection with visual cards (name, avatar placeholder, voice preview)
2. Multi‑character scene setup (drag‑and‑drop characters into a scene)
3. Voice‑cloning interface (drag‑drop audio → preview cloned voice)
4. Live chat interface
   - Highlights the current speaker
   - Shows audio waveform
   - Displays text as it is spoken (word‑level sync – assumed to be provided by the backend)
5. Settings panel (LLM provider, TTS engine, audio output device)

The UI is dark‑mode by default, mobile‑responsive, and hides all technical
details from the user.  All heavy‑lifting (LLM calls, TTS, voice cloning, etc.)
is delegated to the existing `interdimensional-radio` package – this file only
orchestrates the front‑end experience.
"""

import os
import json
import pathlib
import uuid
from typing import List, Dict, Any

import gradio as gr
import numpy as np

# --------------------------------------------------------------------------- #
# Helper utilities – these are deliberately lightweight and can be replaced
# with the real implementations from the Interdimensional Radio code base.
# --------------------------------------------------------------------------- #

PROJECT_ROOT = pathlib.Path(r"D:\codingProjects\interdimensional-radio")
CHARACTER_DIR = PROJECT_ROOT / "characters"

def _load_character_metadata() -> List[Dict[str, Any]]:
    """
    Scan the `characters` folder and build a list of character dicts.
    Expected layout:
        characters/
            <character_name>/
                avatar.png   (optional)
                voice_sample.wav (optional)
                meta.json    (optional, contains {"name": "...", "description": "..."} )
    """
    characters = []
    for char_path in CHARACTER_DIR.iterdir():
        if not char_path.is_dir():
            continue
        meta_path = char_path / "meta.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {"name": char_path.name, "description": ""}

        avatar_path = char_path / "avatar.png"
        avatar_url = None
        if avatar_path.exists():
            avatar_url = str(avatar_path.resolve())

        voice_path = char_path / "voice_sample.wav"
        voice_url = None
        if voice_path.exists():
            voice_url = str(voice_path.resolve())

        characters.append({
            "id": str(uuid.uuid4()),
            "folder": str(char_path),
            "name": meta.get("name", char_path.name),
            "description": meta.get("description", ""),
            "avatar": avatar_url,
            "voice_sample": voice_url,
        })
    return characters

def _preview_voice(voice_path: str):
    """
    Return a Gradio Audio component for previewing a voice sample.
    """
    if not voice_path or not os.path.isfile(voice_path):
        raise gr.Error("Voice sample not found.")
    return voice_path

def _clone_voice(audio_file):
    """
    Stub for voice cloning. In a real implementation this would call the
    Interdimensional Radio voice‑cloning pipeline and return a path to the
    synthesized voice model or a preview audio file.
    """
    # For the demo we simply return the uploaded file as the "cloned" preview.
    return audio_file

def _generate_response(scene_state: List[Dict], user_input: str, settings: Dict):
    """
    Stub that pretends to generate a multi‑character response.
    Returns a list of dicts:
        {"speaker": <character_name>, "text": <string>, "audio": <wav_path>}
    """
    # Very naive demo: each character says the user_input prefixed with their name.
    responses = []
    for char in scene_state:
        # In a real system you would call the LLM + TTS here.
        fake_audio_path = char.get("voice_sample") or ""
        responses.append({
            "speaker": char["name"],
            "text": f"{char['name']} says: {user_input}",
            "audio": fake_audio_path,
        })
    return responses

# --------------------------------------------------------------------------- #
# UI Construction
# --------------------------------------------------------------------------- #

with gr.Blocks(
    title="Interdimensional Radio",
    theme=gr.themes.Base().set(
        background_fill="#1e1e2e",
        primary_hue="slate",
        secondary_hue="slate",
        text_shade="slate",
        font_mono=["JetBrains Mono", "ui-monospace", "Consolas", "monospace"]
    ),
    css="""
    body {margin:0;}
    .dark-mode {background-color:#1e1e2e;color:#e0e0ff;}
    .character-card {border:1px solid #444; border-radius:8px; padding:8px;
        background:#2a2a3a; cursor:grab;}
    .character-card:hover {border-color:#777;}
    .scene-slot {border:2px dashed #555; border-radius:8px; min-height:120px;
        display:flex; align-items:center; justify-content:center;
        color:#777; margin:4px;}
    .scene-slot.filled {border-style:solid; border-color:#888;}
    .chat-bubble {margin:6px 0; padding:8px 12px; border-radius:12px;
        max-width:80%; word-wrap:break-word;}
    .chat-bubble.me {background:#3a3a5a; align-self:flex-end;}
    .chat-bubble.other {background:#2a2a44; align-self:flex-start;}
    .speaker-label {font-weight:600; margin-bottom:4px;}
    """
) as demo:

    # ------------------------------------------------------------------- #
    # Session state initialisation
    # ------------------------------------------------------------------- #
    if "scene" not in gr.State:
        demo.session_state.scene = []  # list of character dicts currently in scene

    # ------------------------------------------------------------------- #
    # Left column – character library
    # ------------------------------------------------------------------- #
    with gr.Column(scale=1, min_width=200):
        gr.Markdown("## 🎭 Characters")
        character_data = _load_character_metadata()

        def _render_character_card(char):
            avatar = char["avatar"] or "https://via.placeholder.com/150?text=No+Avatar"
            return [
                gr.Image(value=avatar, label=char["name"], interactive=False,
                         show_label=False, height=120, width=120,
                         elem_id=f"avatar-{char['id']}"),
                gr.Button("Preview Voice", elem_id=f"preview-{char['id']}"),
                gr.Button("Add to Scene", elem_id=f"add-{char['id']}")
            ]

        # Build a gallery of cards – we use a custom HTML block for drag‑and‑drop
        with gr.Row():
            for char in character_data:
                with gr.Column(scale=0, min_width=150):
                    # Card container
                    with gr.Box(elem_classes="character-card"):
                        avatar = char["avatar"] or "https://via.placeholder.com/150?text=No+Avatar"
                        gr.Image(value=avatar, label=char["name"],
                                 interactive=False, height=120, width=120)
                        gr.Markdown(f"**{char['name']}**")
                        preview_btn = gr.Button("🔊 Preview", size="sm")
                        add_btn = gr.Button("➕ Add", size="sm")

                        # Bind preview
                        preview_btn.click(
                            fn=_preview_voice,
                            inputs=[gr.Text(value=char.get("voice_sample") or "", visible=False)],
                            outputs=gr.Audio(label=f"{char['name']} voice", autoplay=True)
                        )
                        # Bind add‑to‑scene
                        add_btn.click(
                            fn=lambda c=char: c,
                            inputs=None,
                            outputs=gr.State(),
                            queue=False,
                            _js="""
                            (c) => {
                                const ev = new CustomEvent('add-character-to-scene', {detail: c});
                                document.dispatchEvent(ev);
                            }
                            """
                        )

    # ------------------------------------------------------------------- #
    # Center column – scene canvas + voice cloning
    # ------------------------------------------------------------------- #
    with gr.Column(scale=2, min_width=300):
        gr.Markdown("## 🎬 Scene")
        # Scene slots – we allow up to 4 characters side‑by‑side
        scene_slots = []
        with gr.Row():
            for i in range(4):
                slot = gr.Box(
                    elem_id=f"scene-slot-{i}",
                    elem_classes="scene-slot",
                    visible=True
                )
                scene_slots.append(slot)

        # JavaScript listener to receive character drop events
        demo.load(
            fn=lambda: None,
            inputs=None,
            outputs=None,
            _js="""
            () => {
                document.addEventListener('add-character-to-scene', (e) => {
                    const char = e.detail;
                    const event = new CustomEvent('character-dropped', {detail: char});
                    document.dispatchEvent(event);
                });
            }
            """
        )

        # Voice cloning area
        gr.Markdown("### 🗣️ Voice Cloning")
        with gr.Row():
            audio_input = gr.Audio(
                source="upload",
                type="filepath",
                label="Upload a voice sample",
                interactive=True
            )
            clone_btn = gr.Button("Clone Voice")
            cloned_preview = gr.Audio(label="Cloned Voice Preview", interactive=False)

        def _handle_clone(audio):
            if not audio:
                raise gr.Error("Please upload an audio file first.")
            cloned_path = _clone_voice(audio)
            return cloned_path

        clone_btn.click(_handle_clone, inputs=audio_input, outputs=cloned_preview)

    # ------------------------------------------------------------------- #
    # Right column – chat + settings
    # ------------------------------------------------------------------- #
    with gr.Column(scale=2, min_width=300):
        gr.Markdown("## 💬 Live Chat")
        chat_history = gr.Chatbot(
            label="Conversation",
            elem_id="chatbot",
            height=400,
            bubble_full_width=False
        )
        user_msg = gr.Textbox(
            placeholder="Say something...",
            show_label=False,
            container=False
        )
        send_btn = gr.Button("Send", variant="primary")

        # Settings accordion
        with gr.Accordion("⚙️ Settings", open=False):
            llm_provider = gr.Dropdown(
                choices=["OpenAI", "Claude", "Gemini", "Local"],
                value="OpenAI",
                label="LLM Provider"
            )
            tts_engine = gr.Dropdown(
                choices=["ElevenLabs", "Coqui", "OpenAI TTS", "Custom"],
                value="ElevenLabs",
                label="TTS Engine"
            )
            audio_device = gr.Dropdown(
                choices=["Default", "Headphones", "Speakers"],
                value="Default",
                label="Audio Output Device"
            )

        # ---------------------------------------------------------------- #
        # Core chat logic
        # ---------------------------------------------------------------- #
        def _update_scene(state, char):
            """Add character to the scene (max 4)."""
            if len(state) >= 4:
                raise gr.Error("Scene is full (max 4 characters).")
            # Avoid duplicates
            if any(c["id"] == char["id"] for c in state):
                raise gr.Error(f"{char['name']} is already in the scene.")
            state.append(char)
            return state

        def _refresh_scene_display(scene_state):
            """Refresh visual slots – this is done via JS because Gradio lacks direct DOM manipulation."""
            # Return nothing; the JS side will rebuild the slots.
            return None

        # JS to render scene slots
        demo.load(
            fn=_refresh_scene_display,
            inputs=gr.State(),
            outputs=None,
            _js="""
            (scene) => {
                const max = 4;
                for (let i=0; i<max; i++) {
                    const slot = document.getElementById(`scene-slot-${i}`);
                    slot.innerHTML = "";
                    if (scene && scene[i]) {
                        const char = scene[i];
                        const img = document.createElement('img');
                        img.src = char.avatar || 'https://via.placeholder.com/120?text=No+Avatar';
                        img.style.maxWidth='100%';
                        img.style.borderRadius='8px';
                        const name = document.createElement('div');
                        name.textContent = char.name;
                        name.style.textAlign='center';
                        name.style.marginTop='4px';
                        slot.appendChild(img);
                        slot.appendChild(name);
                        slot.classList.add('filled');
                    } else {
                        slot.textContent = "Drop character here";
                        slot.classList.remove('filled');
                    }
                }
            }
            """
        )

        # Listen for character drop events and update scene state
        demo.load(
            fn=_update_scene,
            inputs=[gr.State(), gr.JSON()],
            outputs=gr.State(),
            _js="""
            () => {
                document.addEventListener('character-dropped', (e) => {
                    const char = e.detail;
                    // Send char to backend via hidden component
                    const hidden = document.getElementById('hidden-char-input');
                    hidden.value = JSON.stringify(char);
                    hidden.dispatchEvent(new Event('change'));
                });
            }
            """
        )

        # Hidden component used to pipe JS‑to‑Python character data
        hidden_char_input = gr.Textbox(value="", visible=False, elem_id="hidden-char-input")

        hidden_char_input.change(
            fn=_update_scene,
            inputs=[gr.State(), hidden_char_input],
            outputs=gr.State()
        )

        # Send user message -> generate multi‑character response
        def _handle_user_message(message, scene, settings):
            if not scene:
                raise gr.Error("Add at least one character to the scene first.")
            # Generate a list of responses (speaker, text, audio)
            responses = _generate_response(scene, message, settings)
            # Build chat entries
            chat_updates = []
            for r in responses:
                # Show speaker name as a label
                speaker_label = f"<div class='speaker-label'>{r['speaker']}</div>"
                chat_updates.append((speaker_label + r["text"], r["audio"] if r["audio"] else None))
            return chat_updates, ""

        send_btn.click(
            fn=_handle_user_message,
            inputs=[
                user_msg,
                gr.State(),
                gr.Dict(value={"llm": "OpenAI", "tts": "ElevenLabs", "audio_device": "Default"})
            ],
            outputs=[chat_history, user_msg],
            queue=True
        )

    # ------------------------------------------------------------------- #
    # Global CSS & JavaScript tweaks
    # ------------------------------------------------------------------- #
    demo.load(
        fn=lambda: None,
        inputs=None,
        outputs=None,
        _js="""
        // Make the whole page dark mode (already set via theme)
        document.body.classList.add('dark-mode');
        """
    )

# --------------------------------------------------------------------------- #
# Launch
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    demo.queue(concurrency_count=4).launch(
        server_name="0.0.0.0",
        server_port=7860,
        favicon_path=None,
        debug=False,
        share=False
    )