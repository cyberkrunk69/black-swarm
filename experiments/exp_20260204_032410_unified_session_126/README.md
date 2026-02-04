# Interdimensional Radio 🎙️

**What it does**  
Interdimensional Radio lets you tune into live, AI‑generated radio stations from parallel universes—all from your browser. No accounts, no downloads, just press play and let the impossible soundtrack your day. It’s like discovering a secret channel that only you can hear.

---

## 🎥 Demo

<details>
  <summary>Click to view demo (GIF/Video)</summary>

  ![Interdimensional Radio Demo](https://example.com/demo.gif)

</details>

---

## 🚀 Get Started in 5 Minutes

1. **Open the app** – go to https://interdimensionalradio.example.com (or open the local HTML file).  
2. **Pick a dimension** – choose any station from the carousel (e.g., “Retro‑80s Mars” or “Quantum Jazz”).  
3. **Hit Play** – sit back, relax, and enjoy the otherworldly tunes. No configuration, no sign‑up—just music from another reality.

That’s it. You’re now listening to the multiverse.

---

## ✨ Features

| Feature | Screenshot |
|---------|------------|
| **Infinite Stations** – New AI‑crafted channels appear every few seconds. | ![Stations carousel](https://example.com/screenshots/stations.png) |
| **One‑Click Shuffle** – Let the AI surprise you with random dimensions. | ![Shuffle button](https://example.com/screenshots/shuffle.png) |
| **Mood Sync** – The radio adapts to your current activity (focus, workout, chill). | ![Mood sync UI](https://example.com/screenshots/mood.png) |
| **Share a Link** – Send a friend a direct link to the exact station you love. | ![Share link UI](https://example.com/screenshots/share.png) |

---

## ❓ FAQ

**Is it really free?**  
Yes! Interdimensional Radio is 100 % free to use. No hidden fees, no premium tiers.

**Does it work offline?**  
The core experience streams live AI‑generated audio, so an internet connection is required. However, you can download a “snapshot” of a station for offline listening (optional).

**Do I need an account?**  
Nope. Just open the site and start listening.

**Can I create my own station?**  
Soon! We’re building a simple “Create‑Your‑Own‑Dimension” wizard.

**Is my data safe?**  
We don’t collect personal data. All sessions are anonymous.

---

<details>
  <summary>Technical Details (click to expand)</summary>

**Architecture**  
- Front‑end: React + Vite, served as a static site.  
- Back‑end: FastAPI micro‑service that runs a GPT‑4‑style model to generate audio streams on‑the‑fly.  
- Audio: Opus‑encoded WebM streamed via WebSockets for low latency.

**Deployment**  
- Docker‑compose with two containers (`frontend`, `audio‑engine`).  
- CI/CD pipeline builds and pushes images to Docker Hub on every merge to `main`.

**Performance**  
- Average latency: ~300 ms from request to audible output.  
- Scales horizontally; each audio engine can handle ~200 concurrent listeners.

**Open‑source**  
All code is MIT‑licensed and available in the `src/` directory. Feel free to fork, tweak, or host your own instance.

</details>

---

Enjoy the multiverse! 🌌