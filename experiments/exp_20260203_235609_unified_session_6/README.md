# Interdimensional Radio 🎙️

**What it does**  
Interdimensional Radio streams mind‑bending, AI‑generated music that feels like it was pulled from another universe. No downloads, no accounts—just press play and let the soundscape take over. It’s the easiest way to get a fresh, other‑worldly soundtrack for work, study, or chill sessions.

---

## 🎥 Quick Demo

<details open>
<summary>Watch the magic in action</summary>

[![Interdimensional Radio Demo](https://raw.githubusercontent.com/yourrepo/placeholder/main/demo.gif)](https://www.youtube.com/watch?v=demo_link)

</details>

---

## 🚀 Get Started in 5 Minutes (No setup required)

1. **Open the web app** – click the link below or open `index.html` in your browser.  
2. **Hit “Start Radio”** – the AI instantly begins generating a never‑ending track.  
3. **Adjust the vibe** – slide the “Mood” knob to shift from calm ambient to high‑energy synth.  
4. **Enjoy** – sit back, work, study, or just vibe. The music never repeats and adapts to your chosen mood.

> **Tip:** Keep the tab open and let the radio run in the background for an endless soundtrack.

[Launch Interdimensional Radio →](./index.html)

---

## ✨ Features (with screenshots)

| Feature | Screenshot |
|---------|------------|
| **Infinite AI‑Generated Tracks** | ![Infinite Tracks](https://raw.githubusercontent.com/yourrepo/placeholder/main/feature_infinite.png) |
| **Mood Slider (Calm ↔️ Energetic)** | ![Mood Slider](https://raw.githubusercontent.com/yourrepo/placeholder/main/feature_mood.png) |
| **Visualizer that Reacts to the Music** | ![Visualizer](https://raw.githubusercontent.com/yourrepo/placeholder/main/feature_visualizer.png) |
| **One‑Click Share** – copy a link to the exact session | ![Share Button](https://raw.githubusercontent.com/yourrepo/placeholder/main/feature_share.png) |
| **Offline‑Ready** – cache the last 5 minutes for playback without internet | ![Offline Cache](https://raw.githubusercontent.com/yourrepo/placeholder/main/feature_offline.png) |

---

## ❓ FAQ

**Is it really free?**  
Yes! Interdimensional Radio is 100 % free to use. No hidden fees, no subscriptions.

**Does it work offline?**  
It streams live AI music, but the last 5 minutes are cached locally so you can keep listening if you lose internet for a short time.

**Do I need an account?**  
Nope. Just open the page and start listening.

**Can I use it for commercial projects?**  
The generated music is royalty‑free for personal and commercial use. Feel free to embed it in videos, podcasts, or ads.

**What browsers are supported?**  
Modern browsers with WebAudio support (Chrome, Edge, Firefox, Safari). Mobile browsers work too.

**How does the AI create music so fast?**  
It uses a lightweight, on‑device model that composes in real‑time, backed by a small cloud service for extra variety.

---

## 🛠️ Technical Details (for the curious)

<details>
<summary>Show technical info</summary>

- **Language & Framework:** JavaScript (ES2023) + WebAudio API, React for UI.  
- **AI Model:** Tiny transformer‑based music generator (~2 MB) running in a WebWorker.  
- **Data Flow:** Client‑side generation → optional cloud‑seed for variety (privacy‑first, no logs).  
- **Performance:** < 50 ms latency per bar, < 10 MB RAM usage on average.  
- **Offline Cache:** IndexedDB stores the most recent 5‑minute audio buffer.  
- **License:** MIT (see `LICENSE` file).  

</details>

---

Enjoy the sounds of another dimension! 🌌