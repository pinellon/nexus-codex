from app.chat.study_assistant import detect_study_intent


def test_detect_study_intent_explain():
    payload = detect_study_intent("me explica computacao em nuvem")

    assert payload["intent"] == "explain"
    assert payload["topic"] == "computacao em nuvem"
    assert payload["confidence"] >= 0.8


def test_detect_study_intent_quiz():
    payload = detect_study_intent("cria quiz sobre redes")

    assert payload["intent"] == "quiz"
    assert payload["topic"] == "redes"
    assert payload["confidence"] >= 0.9


def test_detect_study_intent_summarize():
    payload = detect_study_intent("faz um resumo sobre algoritmos")

    assert payload["intent"] == "summarize"
    assert payload["topic"] == "algoritmos"
    assert payload["confidence"] >= 0.85
