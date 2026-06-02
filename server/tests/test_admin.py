from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.deps import get_current_admin_user
from app.api.v1 import admin as admin_api


class _ScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ExecuteResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows if rows is not None else []

    def scalars(self):
        return _ScalarResult(self._rows)

    def scalar_one_or_none(self):
        return self._row


class _FakeSession:
    def __init__(self, execute_result):
        self.execute_result = execute_result
        self.committed = False
        self.refreshed = None

    async def execute(self, _stmt):
        return self.execute_result

    async def commit(self):
        self.committed = True

    async def refresh(self, row):
        self.refreshed = row


@pytest.mark.asyncio
async def test_get_current_admin_user_accepts_hardcoded_admin_email():
    user = SimpleNamespace(email="lhang18022005@gmail.com", full_name="Admin", plan=0)

    result = await get_current_admin_user(current_user=user)

    assert result is user


@pytest.mark.asyncio
async def test_get_current_admin_user_accepts_new_admin_email():
    user = SimpleNamespace(email="23020715@vnu.edu.vn", full_name="New Admin", plan=0)

    result = await get_current_admin_user(current_user=user)

    assert result is user


@pytest.mark.asyncio
async def test_get_current_admin_user_rejects_non_admin_email():
    user = SimpleNamespace(email="regular@example.com", full_name="Regular", plan=1)

    with pytest.raises(HTTPException) as exc:
        await get_current_admin_user(current_user=user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_list_users_returns_rows_from_database():
    rows = [
        SimpleNamespace(id=uuid4(), email="buyer@example.com", full_name="Buyer", plan=0),
        SimpleNamespace(id=uuid4(), email="pro@example.com", full_name="Pro", plan=1),
    ]
    db = _FakeSession(_ExecuteResult(rows=rows))

    result = await admin_api.list_users(db=db, _=SimpleNamespace(email="vinhlg@gmail.com"))

    assert result == rows


@pytest.mark.asyncio
async def test_update_user_plan_changes_plan_and_commits():
    user = SimpleNamespace(id=uuid4(), email="buyer@example.com", full_name="Buyer", plan=0)
    db = _FakeSession(_ExecuteResult(row=user))

    result = await admin_api.update_user_plan(
        user_id=user.id,
        payload=admin_api.UserPlanUpdate(plan=1),
        db=db,
        _=SimpleNamespace(email="vinhlg@gmail.com"),
    )

    assert result.plan == 1
    assert db.committed is True
    assert db.refreshed is user


def test_user_plan_update_rejects_invalid_plan():
    with pytest.raises(ValidationError):
        admin_api.UserPlanUpdate(plan=2)


@pytest.mark.asyncio
async def test_update_user_plan_returns_404_for_missing_user():
    db = _FakeSession(_ExecuteResult(row=None))

    with pytest.raises(HTTPException) as exc:
        await admin_api.update_user_plan(
            user_id=uuid4(),
            payload=admin_api.UserPlanUpdate(plan=1),
            db=db,
            _=SimpleNamespace(email="vinhlg@gmail.com"),
        )

    assert exc.value.status_code == 404
