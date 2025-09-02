
---

# 🎬 YouTube Shorts Generator Agent

Turn long-form videos into **viral-ready YouTube Shorts** with:

* 🎶 Background audio (configurable volume)
* 🎮 Remix mode (stack gameplay with your video)
* 📝 Auto-subtitles with custom fonts, styles & perfect sync
* 🔖 Channel branding (logo, size, opacity)
* ⚙️ Per-account configs (API keys, styles, logos)

Built with **Gemini + LangGraph + Faster-Whisper + FFmpeg**.

---

## 🚀 How to Run

### Single Video

```bash
python main.py --account mychannel --name input/myvideo.mp4
```

### All Videos in Account’s Input Folder

If you don’t give `--name`, the script processes **all videos** inside:

```
./input/mychannel/
```

Example:

```bash
python main.py --account JRE
```

👉 This will loop through every video in `input/JRE/` and generate Shorts.

---

## ⚙️ Config Guide

Each account has a folder inside `config/`.
That folder contains:

* `account.config` → settings for that account
* `logo.png` → your channel logo

### Example `account.config`

```ini
[AzureCredentials]
APIKey = xxxxxxxxxxxxxxxxxxxxxxx
Endpoint = https://xxxxxxx.openai.azure.com/
Deployment = xxxxxxxxxxxxx
version = xxxxx
EmbeddingDeployment = xxxxxxxxxxxxx

[GoogleCred]
GOOGLE_API_KEY = xxxxxxxxxxxxxx
models = gemini-2.0-flash-001, gemini-2.0-pro-exp-02-05

[Subtitles]
font_dir = ./font/Ubuntu-Bold.ttf
color = white
x_pos = center
y_pos = center
font_size = 40
stroke_width = 2
font_window = 7

[Logo]
logo = logo.png
height = 150
opacity = 0.75
x_pos = 850
y_pos = 125

[Prompt]
prompt = The following video is from The Joe Rogan Podcast.

[Trimmer]
clipduration = 240
overlap = 30

[remixdirectory]
_dir = ./remix
vid_frame = 60
type = random
```

---

### 🔑 Sections

**\[AzureCredentials] / \[GoogleCred]** → API keys + LLM settings.
**\[Subtitles]** → Font, color, size, stroke, placement.
**\[Logo]** → Logo path, size, opacity, position.
**\[Prompt]** → Prompt that guides Gemini when selecting clips.
**\[Trimmer]** → Clip length and overlap for chunking.
**\[remixdirectory]** → Gameplay/background folder + style for remix.

---

## 📂 Project Layout

```
shorts-generator/
│── input/
│   └── mychannel/         # Long videos for this account
│── output/
│   └── mychannel/         # Shorts generated here
│── remix/                 # Gameplay/background clips
│── config/
│   └── mychannel/
│       ├── account.config
│       └── logo.png
│── main.py
│── requirements.txt
│── README.md
```

---

🔥 With one command, you can process **one video** or **batch an entire folder**, complete with subtitles, remix gameplay, music, and branding.

---

in tihs i wil remote this adsfas