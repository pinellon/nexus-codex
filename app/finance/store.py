from __future__ import annotations

import json
from pathlib import Path

from app.config import BASE_DIR
from app.finance.models import Bill, Goal, Installment, Transaction


class FinanceStore:
    def __init__(self, base_dir: Path | str | None = None):
        root = Path(base_dir) if base_dir is not None else BASE_DIR
        self.data_dir = root / "data" / "finance"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transactions_path = self.data_dir / "transactions.json"
        self.bills_path = self.data_dir / "bills.json"
        self.installments_path = self.data_dir / "installments.json"
        self.goals_path = self.data_dir / "goals.json"

    def list_transactions(self) -> list[Transaction]:
        return [Transaction(**item) for item in self._read_list(self.transactions_path)]

    def save_transactions(self, items: list[Transaction]) -> None:
        self._write_list(self.transactions_path, [item.to_dict() for item in items])

    def list_bills(self) -> list[Bill]:
        return [Bill(**item) for item in self._read_list(self.bills_path)]

    def save_bills(self, items: list[Bill]) -> None:
        self._write_list(self.bills_path, [item.to_dict() for item in items])

    def list_installments(self) -> list[Installment]:
        return [Installment(**item) for item in self._read_list(self.installments_path)]

    def save_installments(self, items: list[Installment]) -> None:
        self._write_list(self.installments_path, [item.to_dict() for item in items])

    def list_goals(self) -> list[Goal]:
        return [Goal(**item) for item in self._read_list(self.goals_path)]

    def save_goals(self, items: list[Goal]) -> None:
        self._write_list(self.goals_path, [item.to_dict() for item in items])

    def _read_list(self, path: Path) -> list[dict[str, object]]:
        self._ensure_file(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = []
        return data if isinstance(data, list) else []

    def _write_list(self, path: Path, items: list[dict[str, object]]) -> None:
        self._ensure_file(path)
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def _ensure_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("[]\n", encoding="utf-8")
