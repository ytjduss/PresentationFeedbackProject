import whisper


FILLER_WORDS = {
    "어", "음", "그", "저", "아", "에",
    "어음", "으음", "음음", "그그"
}


def format_time(seconds):
    minute = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minute:02d}:{sec:02d}"


def clean_word(word):
    return word.strip(".,!?…~\"'“”‘’()[]{}<> \n\t")


def transcribe_audio(wav_path, model_name="small"):
    model = whisper.load_model(model_name)

    result = model.transcribe(
        str(wav_path),
        language="ko",
        fp16=False,
        temperature=0,
        condition_on_previous_text=False
    )

    return {
        "text": result.get("text", "").strip(),
        "segments": result.get("segments", [])
    }


def detect_text_issues(segments):
    issues = []

    for segment in segments:
        text = segment.get("text", "").strip()
        start = segment.get("start", 0)
        end = segment.get("end", 0)

        words = [clean_word(w) for w in text.split()]
        words = [w for w in words if w]

        for word in words:
            if word in FILLER_WORDS:
                issues.append({
                    "type": "filler",
                    "category": "speech",
                    "label": "간투사",
                    "text": word,
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "time": format_time(start),
                    "message": f"간투사 사용: '{word}'"
                })

        for i in range(len(words) - 1):
            w1 = words[i]
            w2 = words[i + 1]

            if w1 == w2:
                issues.append({
                    "type": "repeat",
                    "category": "speech",
                    "label": "반복 표현",
                    "text": f"{w1} {w2}",
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "time": format_time(start),
                    "message": f"같은 단어 반복 의심: '{w1} {w2}'"
                })

            elif len(w1) == 1 and len(w2) >= 2 and w2.startswith(w1):
                issues.append({
                    "type": "stutter",
                    "category": "speech",
                    "label": "더듬음 의심",
                    "text": f"{w1} {w2}",
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "time": format_time(start),
                    "message": f"첫 음절 반복 의심: '{w1} {w2}'"
                })

    return issues