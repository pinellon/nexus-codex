from datetime import datetime

from app.finance.service import FinanceService


def test_finance_service_persists_summary_and_categories(monkeypatch, tmp_path):
    monkeypatch.setattr("app.finance.service.get_vault_path", lambda: None)
    monkeypatch.setattr("app.finance.service.settings_manager.load", lambda: {"obsidian_enabled": False})

    service = FinanceService(base_dir=tmp_path, now_provider=lambda: datetime(2026, 5, 15, 12, 0, 0))
    service.add_transaction(
        {
            "title": "Pagamento",
            "amount": 2000,
            "type": "income",
            "category": "Trabalho",
            "account": "Nubank",
            "date": "2026-05-05",
        }
    )
    service.add_transaction(
        {
            "title": "Lanche",
            "amount": 35,
            "type": "expense",
            "category": "Alimentacao",
            "account": "Nubank",
            "date": "2026-05-14",
        }
    )
    bill = service.add_bill(
        {
            "title": "Internet",
            "amount": 120,
            "due_date": "2026-05-20",
            "category": "Contas",
            "account": "Nubank",
        }
    )
    goal = service.add_goal(
        {
            "title": "Reserva",
            "target_amount": 500,
            "current_amount": 180,
            "deadline": "2026-05-30",
        }
    )

    summary = service.summary()
    categories = service.categories()
    chart = service.monthly_chart()
    paid_bill = service.pay_bill(bill["id"])

    assert summary["current_balance"] == 1965.0
    assert summary["month_income"] == 2000.0
    assert summary["month_expense"] == 35.0
    assert summary["upcoming_bills_count"] == 1
    assert goal["progress_ratio"] == 0.36
    assert categories["categories"][0]["category"] == "Alimentacao"
    assert chart["points"][13]["expense"] == 35.0
    assert paid_bill["paid"] is True
