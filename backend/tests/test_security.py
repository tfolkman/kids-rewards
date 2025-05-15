from datetime import timedelta

import pytest

from backend.security import (  # Corrected import
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

# Test data
TEST_USER = "testuser"
TEST_PASSWORD = "testpassword"
# It's crucial that the test secret key is also at least 32 characters long
TEST_SECRET_KEY = "testsecretkey_for_pytest_purposes_0123456789"


@pytest.fixture(autouse=True)
def set_test_secret_key(monkeypatch):
    """
    Set the APP_SECRET_KEY environment variable for the duration of the tests in this module.
    This fixture will be automatically used by all tests in this file.
    """
    monkeypatch.setenv("APP_SECRET_KEY", TEST_SECRET_KEY)
    # We need to reload the security module for it to pick up the new env var
    # This is a bit of a hack, a cleaner way might involve structuring your app
    # to allow passing config, but for now, this works for testing.
    import importlib

    from backend import security  # Corrected import

    importlib.reload(security)


def test_password_hashing_and_verification():
    """
    Test that password hashing and verification work correctly.
    """
    hashed_password = get_password_hash(TEST_PASSWORD)
    assert hashed_password is not None
    assert hashed_password != TEST_PASSWORD
    assert verify_password(TEST_PASSWORD, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False


def test_create_and_decode_access_token():
    """
    Test that access tokens can be created and decoded successfully.
    """
    # Reload security module to ensure it uses the monkeypatched SECRET_KEY
    # This is necessary because the module-level SECRET_KEY is set at import time.
    # A more robust solution might involve dependency injection for configuration.
    import importlib

    from backend import security  # Corrected import

    importlib.reload(security)

    token_data = {"sub": TEST_USER, "custom_claim": "test_value"}
    access_token = create_access_token(data=token_data)
    assert access_token is not None

    decoded_username = decode_access_token(access_token)
    assert decoded_username == TEST_USER

    # Test with a specific expiry
    short_expiry_token = create_access_token(data={"sub": "shortliveuser"}, expires_delta=timedelta(seconds=5))
    assert decode_access_token(short_expiry_token) == "shortliveuser"


def test_decode_invalid_token():
    """
    Test that decoding an invalid or malformed token returns None.
    """
    import importlib

    from backend import security  # Corrected import

    importlib.reload(security)

    assert decode_access_token("invalidtoken") is None
    # Create a token with a different key (simulating tampering or wrong key)
    # Note: This requires a bit more setup if jwt.encode is directly used.
    # For simplicity, we'll test with a clearly malformed token.
    # A more advanced test could try to decode a token signed with a different secret.


def test_decode_expired_token(monkeypatch):
    """
    Test that an expired token cannot be decoded.
    """
    import importlib

    from backend import security  # Corrected import

    importlib.reload(security)

    # Create a token that expires very quickly
    expired_token = create_access_token(
        data={"sub": "expireduser"}, expires_delta=timedelta(seconds=-1)
    )  # Expires in the past

    # Attempt to decode - depending on exact timing and leeway, this might still pass
    # if the "exp" check is not immediate. For robust testing, you might need to
    # mock `datetime.now(timezone.utc)` in the security module.
    # For now, we assume a negative delta makes it reliably expired.
    assert decode_access_token(expired_token) is None, "Expired token should not be decodable"

    # A more reliable way to test expiration is to manipulate time with freezegun or similar
    # or by directly checking the 'exp' claim if the decode function returned the full payload.
    # Since decode_access_token only returns username or None, this is the best we can do
    # without modifying the function or adding more complex mocking.


# To run these tests, you would typically navigate to the 'backend' directory
# and run 'pytest' or 'python -m pytest'.
# Ensure APP_SECRET_KEY is set in your environment or use pytest-env.
# The monkeypatch fixture above handles it for these tests.
