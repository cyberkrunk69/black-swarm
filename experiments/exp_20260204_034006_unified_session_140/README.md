# Interdimensional Radio 🎙️  
**Your personal portal to the multiverse of music, podcasts, and live streams—no tech degree required.**  
Just point, click, and let the waves find you.  
All the magic happens in the background, so you can focus on vibing.

---  

## 🎬 Quick Look  

<details open>
  <summary>Click to watch the demo</summary>
  <p align="center">
    <a href="https://www.youtube.com/watch?v=YOUR_DEMO_VIDEO_ID" target="_blank">
      <img src="https://img.youtube.com/vi/YOUR_DEMO_VIDEO_ID/hqdefault.jpg" alt="Interdimensional Radio demo" width="640"/>
    </a>
  </p>
</details>

*(If you prefer a GIF, replace the image above with a GIF URL.)*  

---  

## 🚀 Get Started in 5 Minutes  

1. **Open the app** – double‑click the `Interdimensional Radio` icon.  
2. **Pick a vibe** – choose “Chill”, “Focus”, “Party”, or “Surprise Me”.  
3. **Press Play** – sit back while the app pulls the perfect mix from across dimensions.  

That’s it. No installs, no configs, just instant audio bliss.

---  

## ✨ Features  

| Feature | What You See |
|---------|--------------|
| **Universal Search** | ![Search screenshot](https://via.placeholder.com/400x200?text=Search+UI) |
| **Live Multiverse Streams** | ![Live stream screenshot](https://via.placeholder.com/400x200?text=Live+Stream) |
| **Smart Mixes** | ![Smart mix screenshot](https://via.placeholder.com/400x200?text=Smart+Mix) |
| **Offline Favorites** | ![Offline screenshot](https://via.placeholder.com/400x200?text=Offline+Mode) |
| **One‑Click Sharing** | ![Share screenshot](https://via.placeholder.com/400x200?text=Share) |

*(Replace the placeholder images with real screenshots when available.)*

---  

## ❓ FAQ  

**Is it really free?**  
Yes! All core features are 100 % free. Optional premium skins are available but never required.

**Does it work offline?**  
You can download tracks to your device and enjoy them without an internet connection. Live streams, however, need a connection.

**What platforms does it run on?**  
Windows, macOS, and Linux – the same installer works everywhere.

**Do I need an account?**  
No login, no passwords. Your preferences are stored locally.

**Can I import my own music?**  
Absolutely. Drag‑and‑drop files into the “My Library” tab.

---  

<details>
  <summary>Technical Details (for the curious)</summary>

**Architecture**  
- Built with Python 3.11, leveraging `ffmpeg` for audio decoding.  
- UI powered by `PySide6` (Qt) for a native look on all OSes.  
- Content aggregation uses a lightweight, sandboxed scraper that respects source APIs.

**Security**  
- All network traffic is encrypted (HTTPS).  
- No telemetry; the app never sends personal data.

**Extensibility**  
- Plugins live in `~/.interdimensional_radio/plugins`.  
- Add new source adapters by dropping a Python module that follows the `SourcePlugin` interface.

**Performance**  
- Uses a background thread pool to keep UI snappy.  
- Caches the last 10 GB of streamed content on disk.

</details>

---  

Enjoy the ride—your interdimensional soundtrack awaits!