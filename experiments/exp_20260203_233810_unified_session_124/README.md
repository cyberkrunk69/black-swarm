# Interdimensional Radio

## 🎧 What it does  
Interdimensional Radio turns any text you type into a live, AI‑powered voice broadcast—no microphone, no recording studio needed.  
Just paste a paragraph, hit **Play**, and watch (and hear) the magic happen across the web.  
It’s like having a personal radio host living inside your browser.

---

### 🎬 Demo  
<details open>
  <summary>Click to view demo</summary>
  <p align="center">
    <img src="https://i.imgur.com/placeholder-demo.gif" alt="Interdimensional Radio demo" width="600"/>
  </p>
</details>

---

## 🚀 Get Started in 5 Minutes  

1. **Open the app** – navigate to `http://localhost:8000` (or the hosted link you received).  
2. **Paste your text** – any article, story, or random thoughts.  
3. **Press “Broadcast”** – hear the AI read it out loud instantly.  
4. **Adjust the vibe** – slide the “Tone” and “Speed” knobs to make it sound like a news anchor, a storyteller, or a late‑night DJ.  
5. **Share the link** – copy the generated URL and send it to friends; they’ll hear the same broadcast in real time.

That’s it—no installs, no configs, just pure audio fun.

---

## ✨ Features (with screenshots)

| Feature | Screenshot |
|---------|------------|
| **Instant Text‑to‑Speech** | <img src="https://i.imgur.com/placeholder-tts.png" alt="Instant TTS" width="300"/> |
| **Custom Voice Profiles** | <img src="https://i.imgur.com/placeholder-profiles.png" alt="Voice Profiles" width="300"/> |
| **Live Sync Across Devices** | <img src="https://i.imgur.com/placeholder-sync.png" alt="Live Sync" width="300"/> |
| **One‑Click Sharing** | <img src="https://i.imgur.com/placeholder-share.png" alt="Sharing" width="300"/> |
| **Offline Cache (optional)** | <img src="https://i.imgur.com/placeholder-offline.png" alt="Offline Cache" width="300"/> |

*(Replace the placeholder images with actual screenshots when you ship the next version.)*

---

## ❓ FAQ

**Is it really free?**  
Yes! The core broadcast experience is 100 % free. Premium voice packs are optional but not required.

**Does it work offline?**  
The basic TTS engine runs in the browser, so after the first load you can continue broadcasting without an internet connection (limited to the default voice).

**Do I need an account?**  
No. You can start broadcasting instantly. Creating an account only unlocks saved playlists and custom voice settings.

**Can I embed a broadcast on my website?**  
Absolutely. Click **“Embed”** after you generate a broadcast to get an iframe snippet.

**What browsers are supported?**  
Modern Chrome, Edge, Firefox, and Safari (latest versions). Mobile browsers work too, though the UI is optimized for desktop.

---

## 🛠️ Technical Details (for the curious)

<details>
  <summary>Show technical info</summary>

- **Frontend**: React + Vite, using the Web Speech API for real‑time synthesis.  
- **Backend**: FastAPI (Python) serving a lightweight WebSocket bridge for live sync.  
- **Voice Engine**: OpenAI’s Whisper‑based TTS model, hosted on Azure Functions.  
- **Deployment**: Docker‑compose with Nginx reverse‑proxy; can be run locally with `docker compose up`.  
- **Data Privacy**: All text stays in memory; no logs are persisted unless you enable “Save Broadcast” feature.  

</details>

---

Enjoy turning your thoughts into radio gold! 🎙️