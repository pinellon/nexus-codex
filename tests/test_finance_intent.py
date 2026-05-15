from app.finance.intent import detect_finance_intent


def test_detects_expense_command():
    intent = detect_finance_intent("gastei 35 reais com lanche")

    assert intent is not None
    assert intent.name == "finance_add_expense"
    assert intent.params["amount"] == 35.0
    assert intent.params["category"] == "Alimentacao"


def test_detects_bill_command():
    intent = detect_finance_intent("tenho que pagar 120 reais de internet dia 10")

    assert intent is not None
    assert intent.name == "finance_add_bill"
    assert intent.params["amount"] == 120.0
    assert intent.params["category"] == "Contas"


def test_detects_goal_command():
    intent = detect_finance_intent("cria meta de guardar 500 reais")

    assert intent is not None
    assert intent.name == "finance_add_goal"
    assert intent.params["target_amount"] == 500.0
