import pytest

from app.utils.security import (
    PasswordPolicyError,
    create_access_token,
    decode_access_token,
    generate_random_password,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    validate_password_strength,
    verify_password,
    verify_reset_token,
)


def test_password_hash_roundtrip():
    hashed = hash_password("Sup3rSecret")
    assert hashed != "Sup3rSecret"
    assert verify_password("Sup3rSecret", hashed)
    assert not verify_password("wrong", hashed)


def test_password_hash_is_salted():
    assert hash_password("same-password") != hash_password("same-password")


@pytest.mark.parametrize(
    "password",
    ["short1", "nodigitshere", "12345678", "        "],
)
def test_weak_passwords_rejected(password):
    with pytest.raises(PasswordPolicyError):
        validate_password_strength(password)


def test_strong_password_accepted():
    assert validate_password_strength("Str0ngPass") == "Str0ngPass"


def test_token_roundtrip_carries_claims():
    token = create_access_token(7, "alice", "student", token_version=3)
    payload = decode_access_token(token)
    assert payload["sub"] == 7
    assert payload["username"] == "alice"
    assert payload["role"] == "student"
    assert payload["ver"] == 3


def test_tampered_token_is_rejected():
    token = create_access_token(1, "bob", "admin")
    body, _sig = token.split(".", 1)
    forged = f"{body}.deadbeef"
    with pytest.raises(ValueError):
        decode_access_token(forged)


def test_reset_token_verification():
    token = generate_reset_token()
    stored = hash_reset_token(token)
    assert verify_reset_token(token, stored)
    assert not verify_reset_token("other-token", stored)


def test_generated_password_is_strong_and_unguessable():
    pwd = generate_random_password()
    assert len(pwd) >= 32
    assert generate_random_password() != generate_random_password()
