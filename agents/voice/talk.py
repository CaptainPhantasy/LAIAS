#!/usr/bin/env python3
"""
================================================================================
            FLOYD VOICE — Persistent Conversational Voice Agent
================================================================================
Listen → Transcribe (ElevenLabs STT) → Think (OpenAI) → Speak (ElevenLabs TTS)

Runs as a persistent loop. Press Enter to start listening, speak, then it
responds in voice. Ctrl+C to exit.

Usage:
    python3 talk.py

Requires:
    - sox (brew install sox)
    - ElevenLabs API key (STT + TTS)
    - OpenAI API key (or Portkey virtual key for GPT-4o)
================================================================================
"""

import subprocess
import requests
import json
import os
import sys
import tempfile
import time
import signal

# ============================================================================
# CONFIG
# ============================================================================

ELEVENLABS_KEY = os.environ.get(
    "ELEVENLABS_API_KEY",
    "sk_c0e16c1d9a44a994d3ac72262e86669182f979ce0b13f976"
)
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "W7qwpUg2Mu3kSY99kj9U")

# Load .env from LAIAS project
from dotenv import load_dotenv
load_dotenv("/Volumes/Storage/LAIAS/.env")

PORTKEY_KEY = os.environ.get("PORTKEY_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.portkey.ai/v1")

# Use Portkey if available, fall back to OpenAI direct
if PORTKEY_KEY:
    LLM_KEY = PORTKEY_KEY
    LLM_URL = LLM_BASE_URL
elif OPENAI_KEY:
    LLM_KEY = OPENAI_KEY
    LLM_URL = "https://api.openai.com/v1"
else:
    print("ERROR: No PORTKEY_API_KEY or OPENAI_API_KEY found in .env")
    sys.exit(1)

SYSTEM_PROMPT = """You are Floyd, the AI voice assistant for Legacy AI / Floyd's Labs,
founded by Douglas Talley. You speak in a direct, confident, no-bullshit tone.
You are knowledgeable about:

- LAIAS (Legacy AI Agent Studio) — the platform for generating and deploying AI agents
- Precision Sewer Inspections (PSI) — a sewer inspection company Douglas co-owns
- The agent systems built for SMB automation in Central Indiana
- Website development and white-label solutions for service businesses

You are talking to Douglas and potentially Ryan (the salesperson).
Keep responses concise — you're speaking out loud, not writing an essay.
2-4 sentences max unless asked for detail. Sound like a smart colleague,
not a customer service bot."""

conversation_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

# ============================================================================
# AUDIO FUNCTIONS
# ============================================================================

def record_audio(filepath, silence_duration=1.5, silence_threshold="3%"):
    """Record from mic until silence is detected."""
    print("\n🎤 Listening... (speak now)")
    try:
        subprocess.run([
            "rec", "-q", filepath,
            "rate", "16k",
            "channels", "1",
            "silence", "1", "0.1", silence_threshold,
            "1", str(silence_duration), silence_threshold,
        ], timeout=30, check=True)
    except subprocess.TimeoutExpired:
        print("   (timeout — no speech detected)")
        return False
    except subprocess.CalledProcessError:
        print("   (recording error)")
        return False

    # Check if file has content
    size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    if size < 5000:  # Less than 5KB is probably silence
        print("   (too short, skipping)")
        return False
    return True


def transcribe(filepath):
    """Transcribe audio using ElevenLabs STT."""
    with open(filepath, "rb") as f:
        resp = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": ELEVENLABS_KEY},
            files={"file": ("audio.wav", f, "audio/wav")},
            data={"model_id": "scribe_v1"},
            timeout=30,
        )

    if resp.status_code != 200:
        print(f"   STT error: {resp.status_code} {resp.text[:200]}")
        return ""

    result = resp.json()
    text = result.get("text", "").strip()
    return text


def think(user_text):
    """Send to LLM and get response."""
    conversation_history.append({"role": "user", "content": user_text})

    # Keep conversation history manageable
    messages = conversation_history[-20:]  # Last 20 turns
    messages[0] = conversation_history[0]  # Always include system prompt

    resp = requests.post(
        f"{LLM_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {LLM_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7,
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"   LLM error: {resp.status_code} {resp.text[:200]}")
        return "I didn't catch that. Say it again?"

    reply = resp.json()["choices"][0]["message"]["content"]
    conversation_history.append({"role": "assistant", "content": reply})
    return reply


def speak(text, filepath):
    """Convert text to speech using ElevenLabs TTS and play it."""
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={
            "xi-api-key": ELEVENLABS_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.75,
            }
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"   TTS error: {resp.status_code} {resp.text[:200]}")
        print(f"\n   Floyd: {text}")
        return

    with open(filepath, "wb") as f:
        f.write(resp.content)

    # Play audio
    subprocess.run(["afplay", filepath], check=True)


# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    print("=" * 60)
    print("  FLOYD VOICE — Persistent Conversational Agent")
    print("=" * 60)
    print()
    print("  Press Enter to speak. Ctrl+C to exit.")
    print("  I'll listen until you stop talking, then respond.")
    print()

    # Greeting
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        greeting_file = f.name
    speak("I'm here. What do you need?", greeting_file)
    os.unlink(greeting_file)

    turn = 0
    while True:
        try:
            input("  [Press Enter to speak] ")
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Floyd out.\n")
            break

        turn += 1

        # Record
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            rec_file = f.name

        if not record_audio(rec_file):
            os.unlink(rec_file)
            continue

        # Transcribe
        print("   📝 Transcribing...")
        user_text = transcribe(rec_file)
        os.unlink(rec_file)

        if not user_text:
            print("   (couldn't understand, try again)")
            continue

        print(f"\n   You: {user_text}")

        # Think
        print("   🧠 Thinking...")
        reply = think(user_text)
        print(f"   Floyd: {reply}\n")

        # Speak
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            speak_file = f.name
        speak(reply, speak_file)
        os.unlink(speak_file)


def handle_signal(sig, frame):
    print("\n\n  Floyd out.\n")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)

if __name__ == "__main__":
    main()
