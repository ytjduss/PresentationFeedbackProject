import re
from collections import Counter


STOPWORDS = {
    "그리고", "하지만", "그래서", "저는", "제가", "우리", "여러분",
    "오늘은", "대한", "것을", "수", "있습니다", "합니다", "했습니다",
    "있는", "없는", "통해", "때문에", "또한", "이러한", "서로",
    "더", "많은", "하게", "하는", "하며", "되며"
}


def split_sentences(text):
    sentences = re.split(r"[.!?。！？]\s*", text)
    return [s.strip() for s in sentences if s.strip()]


def extract_keywords(text, top_n=8):
    words = re.findall(r"[가-힣]{2,}", text)

    filtered = []
    for word in words:
        if word not in STOPWORDS:
            filtered.append(word)

    counter = Counter(filtered)
    return [
        {
            "keyword": word,
            "count": count
        }
        for word, count in counter.most_common(top_n)
    ]


def analyze_content(text):
    sentences = split_sentences(text)
    words = text.split()
    keywords = extract_keywords(text)

    word_count = len(words)
    sentence_count = len(sentences)

    if word_count < 100:
        length_label = "짧음"
        length_feedback = "발표 내용이 짧은 편입니다. 핵심 설명을 조금 더 보완하면 좋습니다."
    elif word_count <= 500:
        length_label = "적절"
        length_feedback = "발표 내용 길이가 비교적 적절합니다."
    else:
        length_label = "김"
        length_feedback = "발표 내용이 긴 편입니다. 핵심 내용을 중심으로 줄이면 전달력이 좋아질 수 있습니다."

    if sentence_count == 0:
        avg_words_per_sentence = 0
    else:
        avg_words_per_sentence = word_count / sentence_count

    if avg_words_per_sentence > 25:
        clarity_feedback = "문장이 긴 편입니다. 짧은 문장으로 나누면 이해하기 쉬워집니다."
    else:
        clarity_feedback = "문장 길이는 비교적 무난합니다."

    return {
        "wordCount": word_count,
        "sentenceCount": sentence_count,
        "avgWordsPerSentence": round(avg_words_per_sentence, 2),
        "keywords": keywords,
        "lengthLabel": length_label,
        "lengthFeedback": length_feedback,
        "clarityFeedback": clarity_feedback,
        "contentFeedback": f"{length_feedback} {clarity_feedback}"
    }