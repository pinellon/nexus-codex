from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any
import re

from app.obsidian_memory import normalize

_AMOUNT_RE = re.compile(r"(-?\d+(?:[.,]\d{1,2})?)\s*(?:reais?|r\\$)?", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
_DAY_RE = re.compile(r"\bdia\s+(\d{1,2})\b", re.IGNORECASE)

_CATEGORY_HINTS = {
    "lanche": "Alimentacao",
    "mercado": "Alimentacao",
    "almoco": "Alimentacao",
    "janta": "Alimentacao",
    "internet": "Contas",
    "celular": "Contas",
    "luz": "Contas",
    "agua": "Contas",
    "energia": "Contas",
    "faculdade": "Educacao",
    "curso": "Educacao",
    "uber": "Transporte",
    "onibus": "Transporte",
    "gasolina": "Transporte",
    "notebook": "Tecnologia",
    "pc": "Tecnologia",
    "salario": "Trabalho",
    "pagamento": "Trabalho",
    "freela": "Trabalho",
}


@dataclass(frozen=True)
class FinanceIntent:
    name: str
    params: dict[str, Any] = field(default_factory=dict)


def parse_amount(text: str) -> float | None:
    match = _AMOUNT_RE.search(text)
    if not match:
        return None
    value = match.group(1).replace(".", "").replace(",", ".")
    try:
        return round(abs(float(value)), 2)
    except ValueError:
        return None


def infer_category(label: str, default: str = "Geral") -> str:
    haystack = normalize(label)
    for keyword, category in _CATEGORY_HINTS.items():
        if keyword in haystack:
            return category
    return default


def _title_case(text: str, fallback: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip(" .,!?:;")).strip()
    if not cleaned:
        return fallback
    return cleaned[:1].upper() + cleaned[1:]


def _extract_due_date(text: str, today: date | None = None) -> str:
    today = today or date.today()
    explicit = _DATE_RE.search(text)
    if explicit:
        day = int(explicit.group(1))
        month = int(explicit.group(2))
        year = explicit.group(3)
        if year is None:
            parsed = date(today.year, month, day)
            if parsed < today:
                parsed = date(today.year + 1, month, day)
            return parsed.isoformat()
        parsed_year = int(year)
        if parsed_year < 100:
            parsed_year += 2000
        return date(parsed_year, month, day).isoformat()
    day_match = _DAY_RE.search(text)
    if day_match:
        day = int(day_match.group(1))
        month = today.month
        year = today.year
        if day < today.day:
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
        return date(year, month, day).isoformat()
    return today.isoformat()


def detect_finance_intent(text: str) -> FinanceIntent | None:
    command = normalize(text)
    if not command:
        return None

    if any(fragment in command for fragment in {"resumo financeiro", "saldo do mes", "saldo do mês", "quanto tenho livre", "contas atrasadas"}):
        return FinanceIntent("finance_summary")
    if "quanto gastei" in command or "gastos por categoria" in command or "gastei esse mes" in command or "gastei esse mês" in command:
        return FinanceIntent("finance_category_report")

    if "meta" in command or "guardar" in command:
        amount = parse_amount(command)
        if amount is not None:
            title_match = re.search(r"(?:meta(?: de)?|guardar)\s+(?:de\s+)?(?:r\\$|reais?)?\s*[-\d.,]+\s*(?:reais?)?\s*(?:para\s+)?(.+)?", command)
            title = _title_case(title_match.group(1) if title_match and title_match.group(1) else "Reserva mensal", "Reserva mensal")
            return FinanceIntent(
                "finance_add_goal",
                {
                    "title": title,
                    "target_amount": amount,
                    "current_amount": 0.0,
                    "deadline": "",
                },
            )

    if any(fragment in command for fragment in {"tenho que pagar", "preciso pagar", "conta para pagar", "lembrar de pagar"}):
        amount = parse_amount(command)
        if amount is None:
            return None
        title_match = re.search(r"(?:pagar)\s+(?:r\\$|reais?)?\s*[-\d.,]+\s*(?:reais?)?\s*(?:de|da|do|para)?\s*(.+?)(?:\s+dia\s+\d{1,2}|\s+\d{1,2}/\d{1,2}(?:/\d{2,4})?)?$", command)
        title = _title_case(title_match.group(1) if title_match else "Conta pendente", "Conta pendente")
        return FinanceIntent(
            "finance_add_bill",
            {
                "title": title,
                "amount": amount,
                "due_date": _extract_due_date(command),
                "category": infer_category(title, default="Contas"),
                "account": "",
            },
        )

    if "paguei a conta" in command or "marcar conta" in command or "conta paga" in command:
        title_match = re.search(r"(?:conta(?:\s+de)?|fatura(?:\s+de)?)\s+(.+)", command)
        title = _title_case(title_match.group(1) if title_match else "", "")
        return FinanceIntent("finance_pay_bill", {"title": title})

    if command.startswith("recebi") or command.startswith("ganhei") or " caiu " in f" {command} " or " entrou " in f" {command} ":
        amount = parse_amount(command)
        if amount is None:
            return None
        title_match = re.search(r"(?:recebi|ganhei|caiu|entrou)\s+(?:r\\$|reais?)?\s*[-\d.,]+\s*(?:reais?)?\s*(?:de|da|do|por)?\s*(.+)?", command)
        title = _title_case(title_match.group(1) if title_match and title_match.group(1) else "Entrada", "Entrada")
        return FinanceIntent(
            "finance_add_income",
            {
                "title": title,
                "amount": amount,
                "category": infer_category(title, default="Receitas"),
                "account": "",
            },
        )

    if any(fragment in command for fragment in {"gastei", "comprei", "paguei"}) and "conta" not in command:
        amount = parse_amount(command)
        if amount is None:
            return None
        title_match = re.search(r"(?:gastei|comprei|paguei)\s+(?:r\\$|reais?)?\s*[-\d.,]+\s*(?:reais?)?\s*(?:com|em|de)?\s*(.+)?", command)
        title = _title_case(title_match.group(1) if title_match and title_match.group(1) else "Gasto", "Gasto")
        return FinanceIntent(
            "finance_add_expense",
            {
                "title": title,
                "amount": amount,
                "category": infer_category(title, default="Geral"),
                "account": "",
            },
        )

    if "financeiro" in command or "financas" in command or "finanças" in command:
        return FinanceIntent("finance_summary")

    return None
