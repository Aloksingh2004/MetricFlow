import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from app.config import Settings
from app.models import User
from app.services import auth


class FakeDb:
    def __init__(self, user: User | None):
        self.user = user

    def get(self, model, user_id):
        return self.user if self.user and self.user.id == user_id else None


def test_access_token_identifies_active_user():
    user = User(id="user-1", email="owner@example.com", password_hash="hash", role="owner", is_active=True)
    token, expires_in = auth.create_access_token(user)

    current_user = auth.get_current_user(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
        FakeDb(user),
    )

    assert current_user.id == "user-1"
    assert expires_in == 1800


def test_invalid_token_is_rejected():
    with pytest.raises(HTTPException) as error:
        auth.get_current_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-token"),
            FakeDb(None),
        )

    assert error.value.status_code == 401


def test_inactive_user_cannot_use_valid_token():
    inactive = User(id="user-2", email="inactive@example.com", password_hash="hash", is_active=False)
    token, _ = auth.create_access_token(inactive)

    with pytest.raises(HTTPException) as error:
        auth.get_current_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            FakeDb(inactive),
        )

    assert error.value.status_code == 401


@pytest.mark.parametrize(
    "secret_key",
    ["development-only-secret-change-before-production", "replace-this-" + "a" * 32],
)
def test_production_rejects_known_unsafe_secrets(secret_key):
    with pytest.raises(ValidationError):
        Settings(app_env="production", secret_key=secret_key)
