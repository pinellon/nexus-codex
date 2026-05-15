from __future__ import annotations

from calendar import monthrange
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
import re

from app.finance.intent import infer_category
from app.finance.models import Bill, Goal, Transaction, new_finance_id, utc_timestamp
from app.finance.store import FinanceStore
from app.obsidian_memory import get_vault_path
import app.settings_manager as settings_manager


def _money(value: float) -> str:
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _coerce_amount(value: Any) -> float:
    if isinstance(value, (int, float)):
        return round(abs(float(value)), 2)
    text = str(value or "").strip().replace("R$", "").replace("r$", "").replace(" ", "")
    if not text:
        return 0.0
    normalized = text.replace(".", "").replace(",", ".")
    return round(abs(float(normalized)), 2)


def _coerce_date(value: Any, fallback: date) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback.isoformat()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", text):
        day, month, year = text.split("/")
        return date(int(year), int(month), int(day)).isoformat()
    if re.fullmatch(r"\d{2}/\d{2}", text):
        day, month = text.split("/")
        candidate = date(fallback.year, int(month), int(day))
        if candidate < fallback:
            candidate = date(fallback.year + 1, int(month), int(day))
        return candidate.isoformat()
    return fallback.isoformat()


def _parse_iso_day(value: str) -> date:
    return date.fromisoformat(value[:10])


class FinanceService:
    def __init__(
        self,
        base_dir: Path | str | None = None,
        store: FinanceStore | None = None,
        now_provider=None,
    ):
        self.store = store or FinanceStore(base_dir=base_dir)
        self._now_provider = now_provider or datetime.now

    def list_transactions(self) -> list[dict[str, object]]:
        items = sorted(self.store.list_transactions(), key=lambda item: (item.date, item.created_at, item.id), reverse=True)
        return [item.to_dict() for item in items]

    def add_transaction(self, payload: dict[str, Any]) -> dict[str, object]:
        now = self._now_provider()
        transaction = Transaction(
            id=new_finance_id("txn"),
            title=str(payload.get("title") or "Movimento").strip() or "Movimento",
            amount=_coerce_amount(payload.get("amount")),
            type=str(payload.get("type") or "expense").strip() or "expense",
            category=str(payload.get("category") or infer_category(str(payload.get("title") or ""))).strip() or "Geral",
            account=str(payload.get("account") or "Conta principal").strip() or "Conta principal",
            date=_coerce_date(payload.get("date"), now.date()),
            notes=str(payload.get("notes") or "").strip(),
            finance_type=str(payload.get("finance_type") or "variable").strip() or "variable",
            created_at=utc_timestamp(now),
        )
        items = self.store.list_transactions()
        items.append(transaction)
        self.store.save_transactions(items)
        self._write_obsidian_transaction(transaction)
        return transaction.to_dict()

    def list_bills(self) -> list[dict[str, object]]:
        items = sorted(self.store.list_bills(), key=lambda item: (item.paid, item.due_date, item.title.lower()))
        return [item.to_dict() for item in items]

    def add_bill(self, payload: dict[str, Any]) -> dict[str, object]:
        now = self._now_provider()
        bill = Bill(
            id=new_finance_id("bill"),
            title=str(payload.get("title") or "Conta").strip() or "Conta",
            amount=_coerce_amount(payload.get("amount")),
            due_date=_coerce_date(payload.get("due_date"), now.date()),
            paid=bool(payload.get("paid", False)),
            recurrence=str(payload.get("recurrence") or "none").strip() or "none",
            account=str(payload.get("account") or "Conta principal").strip() or "Conta principal",
            category=str(payload.get("category") or infer_category(str(payload.get("title") or ""), default="Contas")).strip() or "Contas",
            notes=str(payload.get("notes") or "").strip(),
            created_at=utc_timestamp(now),
            paid_at=str(payload.get("paid_at") or "") or None,
        )
        items = self.store.list_bills()
        items.append(bill)
        self.store.save_bills(items)
        self._write_obsidian_bill(bill)
        return bill.to_dict()

    def pay_bill(self, bill_id_or_title: str) -> dict[str, object]:
        items = self.store.list_bills()
        needle = str(bill_id_or_title or "").strip().lower()
        if not needle:
            raise ValueError("Informe a conta que deve ser marcada como paga.")
        target_index = -1
        for index, item in enumerate(items):
            if item.id.lower() == needle or item.title.lower() == needle or needle in item.title.lower():
                target_index = index
                break
        if target_index < 0:
            raise ValueError("Conta nao encontrada.")
        updated = replace(items[target_index], paid=True, paid_at=utc_timestamp(self._now_provider()))
        items[target_index] = updated
        self.store.save_bills(items)
        self._write_obsidian_bill(updated)
        return updated.to_dict()

    def list_goals(self) -> list[dict[str, object]]:
        items = sorted(self.store.list_goals(), key=lambda item: (item.deadline, item.title.lower()))
        return [self._goal_to_dict(item) for item in items]

    def add_goal(self, payload: dict[str, Any]) -> dict[str, object]:
        now = self._now_provider()
        goal = Goal(
            id=new_finance_id("goal"),
            title=str(payload.get("title") or "Meta financeira").strip() or "Meta financeira",
            target_amount=_coerce_amount(payload.get("target_amount")),
            current_amount=_coerce_amount(payload.get("current_amount")),
            deadline=_coerce_date(payload.get("deadline"), now.date() + timedelta(days=30)),
            notes=str(payload.get("notes") or "").strip(),
            created_at=utc_timestamp(now),
        )
        items = self.store.list_goals()
        items.append(goal)
        self.store.save_goals(items)
        self._write_obsidian_goal(goal)
        return self._goal_to_dict(goal)

    def summary(self, reference_date: date | None = None) -> dict[str, object]:
        today = reference_date or self._now_provider().date()
        transactions = self.store.list_transactions()
        bills = self.store.list_bills()
        installments = self.store.list_installments()
        goals = self.store.list_goals()

        month_key = today.strftime("%Y-%m")
        balance = 0.0
        month_income = 0.0
        month_expense = 0.0
        for item in transactions:
            signed_amount = item.amount if item.type == "income" else -item.amount
            balance += signed_amount
            if item.date.startswith(month_key):
                if item.type == "income":
                    month_income += item.amount
                else:
                    month_expense += item.amount

        overdue_bills = [bill for bill in bills if not bill.paid and _parse_iso_day(bill.due_date) < today]
        upcoming_bills = [
            bill
            for bill in bills
            if not bill.paid and today <= _parse_iso_day(bill.due_date) <= today + timedelta(days=14)
        ]
        unpaid_this_month = [
            bill
            for bill in bills
            if not bill.paid and bill.due_date.startswith(month_key) and _parse_iso_day(bill.due_date) >= today
        ]
        active_installments = [item for item in installments if item.current_installment <= item.total_installments]
        available = balance - sum(bill.amount for bill in unpaid_this_month) - sum(item.installment_amount for item in active_installments)

        return {
            "month_label": today.strftime("%m/%Y"),
            "current_balance": round(balance, 2),
            "month_income": round(month_income, 2),
            "month_expense": round(month_expense, 2),
            "available_until_month_end": round(available, 2),
            "upcoming_bills_count": len(upcoming_bills),
            "upcoming_bills_amount": round(sum(bill.amount for bill in upcoming_bills), 2),
            "overdue_bills_count": len(overdue_bills),
            "overdue_bills_amount": round(sum(bill.amount for bill in overdue_bills), 2),
            "active_installments_count": len(active_installments),
            "active_installments_amount": round(sum(item.installment_amount for item in active_installments), 2),
            "upcoming_bills": [bill.to_dict() for bill in sorted(upcoming_bills, key=lambda item: item.due_date)[:5]],
            "overdue_bills": [bill.to_dict() for bill in sorted(overdue_bills, key=lambda item: item.due_date)[:5]],
            "goals": [self._goal_to_dict(item) for item in goals],
        }

    def monthly_chart(self, reference_date: date | None = None) -> dict[str, object]:
        today = reference_date or self._now_provider().date()
        first_day = date(today.year, today.month, 1)
        days_in_month = monthrange(today.year, today.month)[1]
        last_day = date(today.year, today.month, days_in_month)
        transactions = self.store.list_transactions()

        opening_balance = 0.0
        for item in transactions:
            transaction_day = _parse_iso_day(item.date)
            signed = item.amount if item.type == "income" else -item.amount
            if transaction_day < first_day:
                opening_balance += signed

        points: list[dict[str, object]] = []
        running_balance = opening_balance
        for day_number in range(1, days_in_month + 1):
            cursor = date(today.year, today.month, day_number)
            incomes = 0.0
            expenses = 0.0
            for item in transactions:
                transaction_day = _parse_iso_day(item.date)
                if transaction_day != cursor:
                    continue
                if item.type == "income":
                    incomes += item.amount
                    running_balance += item.amount
                else:
                    expenses += item.amount
                    running_balance -= item.amount
            points.append(
                {
                    "date": cursor.isoformat(),
                    "label": f"{day_number:02d}/{today.month:02d}",
                    "balance": round(running_balance, 2),
                    "income": round(incomes, 2),
                    "expense": round(expenses, 2),
                    "is_future": cursor > today,
                }
            )

        return {
            "start_date": first_day.isoformat(),
            "end_date": last_day.isoformat(),
            "points": points,
            "opening_balance": round(opening_balance, 2),
        }

    def categories(self, reference_date: date | None = None) -> dict[str, object]:
        today = reference_date or self._now_provider().date()
        month_key = today.strftime("%Y-%m")
        totals: dict[str, float] = {}
        by_account: dict[str, float] = {}
        for item in self.store.list_transactions():
            if item.type != "expense" or not item.date.startswith(month_key):
                continue
            totals[item.category] = round(totals.get(item.category, 0.0) + item.amount, 2)
            by_account[item.account] = round(by_account.get(item.account, 0.0) + item.amount, 2)
        categories = [
            {"category": name, "amount": amount}
            for name, amount in sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
        ]
        accounts = [
            {"account": name, "amount": amount}
            for name, amount in sorted(by_account.items(), key=lambda pair: pair[1], reverse=True)
        ]
        return {"categories": categories, "accounts": accounts}

    def execute_intent(self, intent_name: str, params: dict[str, Any]) -> str:
        if intent_name == "finance_add_expense":
            item = self.add_transaction({**params, "type": "expense", "finance_type": params.get("finance_type", "variable")})
            return f"Gasto registrado: {item['title']} em {item['category']} por {_money(float(item['amount']))}."
        if intent_name == "finance_add_income":
            item = self.add_transaction({**params, "type": "income", "finance_type": params.get("finance_type", "variable")})
            return f"Entrada registrada: {item['title']} por {_money(float(item['amount']))}."
        if intent_name == "finance_add_bill":
            bill = self.add_bill({**params, "recurrence": params.get("recurrence", "monthly")})
            return f"Conta registrada: {bill['title']} vence em {bill['due_date']} por {_money(float(bill['amount']))}."
        if intent_name == "finance_pay_bill":
            bill = self.pay_bill(str(params.get("title") or params.get("id") or ""))
            return f"Conta marcada como paga: {bill['title']}."
        if intent_name == "finance_add_goal":
            goal = self.add_goal(params)
            return f"Meta criada: {goal['title']} com alvo de {_money(float(goal['target_amount']))}."
        if intent_name in {"finance_summary", "finance_category_report"}:
            summary = self.summary()
            categories = self.categories()["categories"]
            lines = [
                f"Saldo atual: {_money(float(summary['current_balance']))}",
                f"Entradas do mes: {_money(float(summary['month_income']))}",
                f"Saidas do mes: {_money(float(summary['month_expense']))}",
                f"Livre ate o fim do mes: {_money(float(summary['available_until_month_end']))}",
            ]
            if summary["upcoming_bills_count"]:
                lines.append(
                    f"Contas proximas: {summary['upcoming_bills_count']} somando {_money(float(summary['upcoming_bills_amount']))}"
                )
            if summary["overdue_bills_count"]:
                lines.append(
                    f"Contas atrasadas: {summary['overdue_bills_count']} somando {_money(float(summary['overdue_bills_amount']))}"
                )
            if categories:
                top = categories[0]
                lines.append(f"Categoria com maior gasto no mes: {top['category']} ({_money(float(top['amount']))}).")
            return "\n".join(lines)
        raise ValueError(f"Intento financeiro nao suportado: {intent_name}")

    def _goal_to_dict(self, goal: Goal) -> dict[str, object]:
        target = max(goal.target_amount, 0.01)
        progress_ratio = min(max(goal.current_amount / target, 0.0), 1.0)
        return {
            **goal.to_dict(),
            "progress_ratio": round(progress_ratio, 4),
            "remaining_amount": round(max(goal.target_amount - goal.current_amount, 0.0), 2),
        }

    def _obsidian_enabled(self) -> bool:
        settings = settings_manager.load()
        return bool(settings.get("obsidian_enabled", True)) and get_vault_path() is not None

    def _write_obsidian_transaction(self, item: Transaction) -> None:
        body = (
            "---\n"
            "type: finance\n"
            f"entry_type: {item.type}\n"
            f"amount: {item.amount}\n"
            f"category: {item.category}\n"
            f"account: {item.account}\n"
            f"date: {item.date}\n"
            "tags:\n"
            "  - nexus\n"
            "  - financeiro\n"
            f"  - {'receita' if item.type == 'income' else 'gasto'}\n"
            "---\n\n"
            f"# {item.title}\n\n"
            f"Valor: {_money(item.amount)}\n"
            f"Conta: {item.account}\n"
            f"Categoria: {item.category}\n"
            f"Data: {item.date}\n"
        )
        self._write_obsidian_note("Transacoes", item.date, item.title, body)

    def _write_obsidian_bill(self, item: Bill) -> None:
        body = (
            "---\n"
            "type: finance_bill\n"
            f"amount: {item.amount}\n"
            f"category: {item.category}\n"
            f"account: {item.account}\n"
            f"date: {item.due_date}\n"
            f"status: {'paid' if item.paid else 'pending'}\n"
            "tags:\n"
            "  - nexus\n"
            "  - financeiro\n"
            "  - conta\n"
            "---\n\n"
            f"# {item.title}\n\n"
            f"Valor: {_money(item.amount)}\n"
            f"Conta: {item.account}\n"
            f"Categoria: {item.category}\n"
            f"Vencimento: {item.due_date}\n"
            f"Status: {'paga' if item.paid else 'pendente'}\n"
        )
        self._write_obsidian_note("Contas", item.due_date, item.title, body)

    def _write_obsidian_goal(self, item: Goal) -> None:
        body = (
            "---\n"
            "type: finance_goal\n"
            f"amount: {item.target_amount}\n"
            f"date: {item.deadline}\n"
            "status: active\n"
            "tags:\n"
            "  - nexus\n"
            "  - financeiro\n"
            "  - meta\n"
            "---\n\n"
            f"# {item.title}\n\n"
            f"Meta: {_money(item.target_amount)}\n"
            f"Atual: {_money(item.current_amount)}\n"
            f"Prazo: {item.deadline}\n"
        )
        self._write_obsidian_note("Metas", item.deadline, item.title, body)

    def _write_obsidian_note(self, section: str, stamp: str, title: str, body: str) -> None:
        if not self._obsidian_enabled():
            return
        vault = get_vault_path()
        if not vault:
            return
        folder = vault / "NEXUS" / "Financeiro" / section
        folder.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r"[^a-zA-Z0-9 _.-]+", "", title).strip().replace(" ", "-") or "registro"
        path = folder / f"{stamp} - {safe_title}.md"
        path.write_text(body, encoding="utf-8")
