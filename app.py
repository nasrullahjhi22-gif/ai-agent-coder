import subprocess
import time
import random
import requests
import re

# ==========================================================
# KONFIGURASI BOT
# ==========================================================
CLICK_X = 554
CLICK_Y = 1048

NUM_RECENT_COMMENTS = 30
WAIT_PAGE_LOAD = 10
WAIT_CYCLE_MIN = 2
WAIT_CYCLE_MAX = 10

# ==========================================================
# UTILITY FUNCTIONS (WAYLAND/HYPRLAND)
# ==========================================================

def wtype_key(key):
    subprocess.run(["wtype", "-k", key])

def wtype_shortcut(modifier, key):
    subprocess.run(["wtype", "-M", modifier, key, "-m", modifier])

def perform_focus(x, y):
    # Pindah kursor dan klik untuk fokus ke window/elemen
    subprocess.run(["hyprctl", "dispatch", "movecursor", f"{x} {y}"])
    time.sleep(0.3)
    for _ in range(3):
        subprocess.run(["ydotool", "click", "0xC0"])
        time.sleep(0.05)

# ==========================================================
# TEXT CLEANING
# ==========================================================

def sanitize_text(text):
    # Membersihkan teks input agar tidak merusak prompt AI
    # Membiarkan tanda tanya dan titik untuk konteks
    text = re.sub(r'[^a-zA-Z0-9 ?.!]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_prompt(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ==========================================================
# CLIPBOARD & PARSING
# ==========================================================

def get_clipboard():
    try:
        result = subprocess.run(["wl-paste"], capture_output=True, text=True, check=True)
        return result.stdout
    except:
        return ""

def parse_comments(raw_text):
    lines = raw_text.splitlines()
    comments = []
    junk_words = ["buffering", "member", "joined", "xp", "idr", "donate", "welcome to live chat"]

    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith("@"): 
            try:
                for j in range(1, 4):
                    if i + j < len(lines):
                        pot = sanitize_text(lines[i + j])
                        is_junk = any(junk in pot.lower() for junk in junk_words)
                        if (pot and not pot.startswith("@") and not is_junk and not pot.isdigit()):
                            pot = re.sub(r'(.)\1{3,}', r'\1\1', pot)
                            comments.append(pot)
                            break
            except:
                pass
    return list(dict.fromkeys(comments))

# ==========================================================
# MULTILINGUAL AI GENERATOR (STANDARD EMOJI)
# ==========================================================

def generate_ai_comment(chat_history):
    context = " | ".join(chat_history[-NUM_RECENT_COMMENTS:])
    context = context
    print("Contex:", context)
    
    url = "https://antigravity-manager-production-2001.up.railway.app/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-f71167bc6651472694d585a7174e91cb"
    }

    # Instruksi yang meminta AI menggunakan emoji standar secara natural
    system_instruction = (
	"You are a viewer participating in a YouTube live stream chat.\n"

	"Task:\n"
	"Generate ONE short, berbaurlah dengan komentar-komentar yang lain, gunakan kalimat yang bisa membuatmu tidak berbeda dengan komentar yang lain\n"

	"Language Rules:\n"
	"- Analyze the provided context.\n"
	"- Detect all languages used in the context.\n"
	"- If the dominant language is unclear, default to English.\n"

	"Style Rules:\n"
	"- Match the vibe, tone, and style of the chat context.\n"
	"- The comment should feel like it was written by a real viewer.\n"
	"- It can be funny, surprised, sarcastic, or reactive depending on the context, not repitition.\n"
	"- Length: 2–12 words.\n"
	"- Internet slang is allowed.\n"
	"- Letter casing (lowercase or uppercase) should match the style used in the context.\n"

	"Emoji Rules:\n"
	"- Optional: 0–2 emojis.\n"
	"- use chat emojis if they fit the vibe, not everytime.\n"

	"Strict Output Rules:\n"
	"- Output ONLY the comment.\n"
	"- No explanations.\n"
	"- No quotes.\n"
	"- No extra text.\n"
	"- No line breaks.\n"
    )

    payload = {
        "model": "gemini-3-flash",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Chat context: {context}"}
        ],
        "temperature": 0.8
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            res = r.json()["choices"][0]["message"]["content"]
            return res.replace('"', '').strip()
        else:
            return "mantap 🔥"
    except:
        return "wkwkwk 😂"

# ==========================================================
# MAIN LOOP
# ==========================================================

def main():
    print("--- Bot Aktif (Standard Emoji & Multilingual) ---")
    time.sleep(2)
    ngulang = 1
    while True:
        print(f"\n[{ngulang}] [Siklus Baru] Membaca chat...")
        time.sleep(WAIT_PAGE_LOAD)
        
        # Ambil chat (Copy all)
        perform_focus(CLICK_X, CLICK_Y - 150)
        time.sleep(0.5)
        wtype_shortcut("ctrl", "a")
        time.sleep(0.3)
        wtype_shortcut("ctrl", "c")
        time.sleep(0.5)

        raw_text = get_clipboard()
        history = parse_comments(raw_text)

        if len(history) < 3:
            print("Chat tidak cukup. Skip...")
        else:
            ai_msg = generate_ai_comment(history)
            print("AI Mengatakan:", ai_msg)

            # Paste ke kolom chat
            perform_focus(CLICK_X, CLICK_Y)
            time.sleep(0.8)
            
            subprocess.run(["wl-copy", ai_msg])
            time.sleep(0.5)
            wtype_shortcut("ctrl", "v")
            time.sleep(0.5)
            wtype_key("Return")
            print(">>> Komentar terkirim!")

        delay = random.uniform(WAIT_CYCLE_MIN, WAIT_CYCLE_MAX)
        print(f"Menunggu {delay:.2f} detik...")
        ngulang+=1
        time.sleep(delay)

if __name__ == "__main__":
    main()
