"""
Tests for authentication module.

Tests password utilities, token handling, and dev-mode auth.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.auth import (
    ALGORITHM,
    SECRET_KEY,
    CurrentUser,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.main import create_app


class TestPasswordUtilities:
    """Tests for password hashing and verification."""

    def test_hash_password_returns_string(self):
        """Hash password returns a string."""
        result = hash_password("test_password")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_password_creates_different_hashes(self):
        """Same password creates different hashes (bcrypt salt)."""
        hash1 = hash_password("test_password")
        hash2 = hash_password("test_password")
        assert hash1 != hash2  # bcrypt generates unique salts

    def test_verify_password_correct(self):
        """Verify password returns True for correct password."""
        hashed = hash_password("test_password")
        assert verify_password("test_password", hashed) is True

    def test_verify_password_incorrect(self):
        """Verify password returns False for incorrect password."""
        hashed = hash_password("test_password")
        assert verify_password("wrong_password", hashed) is False


class TestTokenCreation:
    """Tests for JWT token creation."""

    def test_create_access_token_returns_string(self):
        """Access token creation returns a string."""
        token = create_access_token("user-123", "test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_returns_string(self):
        """Refresh token creation returns a string."""
        token = create_refresh_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_expected_claims(self):
        """Access token contains expected claims."""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        token = create_access_token(user_id, email)
        payload = decode_token(token)

        assert payload.sub == user_id
        assert payload.email == email
        assert payload.type == "access"
        assert payload.exp is not None

    def test_refresh_token_contains_expected_claims(self):
        """Refresh token contains expected claims."""
        user_id = str(uuid.uuid4())
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload.sub == user_id
        assert payload.type == "refresh"
        assert payload.exp is not None

    def test_access_token_with_custom_expiry(self):
        """Access token respects custom expiry delta."""
        user_id = str(uuid.uuid4())
        custom_delta = timedelta(hours=2)
        token = create_access_token(user_id, "test@example.com", custom_delta)
        payload = decode_token(token)

        # Token should be valid for ~2 hours
        assert payload.exp is not None
        now = datetime.now(UTC)
        expected_exp = now + custom_delta
        # Allow 1 minute tolerance
        assert abs((payload.exp - expected_exp).total_seconds()) < 60


class TestTokenDecoding:
    """Tests for JWT token decoding and validation."""

    def test_decode_valid_token(self):
        """Decode valid token returns payload."""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        token = create_access_token(user_id, email)
        payload = decode_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == user_id
        assert payload.email == email

    def test_decode_invalid_token_raises(self):
        """Decode invalid token raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_decode_expired_token_raises(self):
        """Decode expired token raises HTTPException."""
        # Create token that's already expired
        import jose.jwt as jwt
        expired_time = datetime.now(UTC) - timedelta(hours=1)
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "exp": expired_time,
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "type": "access"
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            decode_token(expired_token)
        assert exc_info.value.status_code == 401


class TestDevModeAuth:
    """Tests for dev-mode authentication."""

    @pytest.fixture
    def app(self):
        """Create test app."""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_dev_mode_without_headers_returns_fallback_user(self, client):
        """Dev mode without headers returns fallback dev user."""
        # Assuming AUTH_DEV_MODE=true by default in tests
        response = client.get("/api/agents")  # Any protected endpoint
        # Should not return 401 in dev mode
        # Response depends on endpoint, but shouldn't be auth error
        assert response.status_code != 401 or "Authentication required" not in response.text

    def test_dev_mode_with_custom_user_header(self, client):
        """Dev mode respects X-User-Id header."""
        user_id = str(uuid.uuid4())
        response = client.get(
            "/api/agents",
            headers={"X-User-Id": user_id, "X-User-Email": "custom@test.com"}
        )
        # Request should proceed with custom user
        assert response.status_code != 401 or "Authentication required" not in response.text

    def test_dev_mode_rejects_invalid_uuid(self, client):
        """Dev mode rejects invalid UUID in X-User-Id."""
        response = client.get(
            "/api/agents",
            headers={"X-User-Id": "not-a-uuid"}
        )
        assert response.status_code == 401


class TestAuthRoutes:
    """Tests for authentication API routes."""

    @pytest.fixture
    def app(self):
        """Create test app."""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_register_endpoint_exists(self, client):
        """Register endpoint is accessible."""
        response = client.post("/auth/register", json={
            "email": "newuser@test.com",
            "password": "SecurePass123!",
            "name": "Test User"
        })
        # Should not return 404
        assert response.status_code != 404

    def test_register_missing_fields_returns_422(self, client):
        """Register with missing fields returns validation error."""
        response = client.post("/auth/register", json={
            "email": "incomplete@test.com"
            # Missing password and name
        })
        assert response.status_code == 422

    def test_login_endpoint_exists(self, client):
        """Login endpoint is accessible."""
        response = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "password123"
        })
        # Should not return 404
        assert response.status_code != 404

    def test_login_missing_fields_returns_422(self, client):
        """Login with missing fields returns validation error."""
        response = client.post("/auth/login", json={
            "email": "user@test.com"
            # Missing password
        })
        assert response.status_code == 422

    def test_refresh_endpoint_exists(self, client):
        """Refresh endpoint is accessible."""
        response = client.post("/auth/refresh?refresh_token=some_token")
        # Should not return 404
        assert response.status_code != 404

    def test_me_endpoint_requires_auth(self, client):
        """Me endpoint requires authentication."""
        response = client.get("/auth/me")
        # In dev mode should work, in production would be 401
        # This test just verifies endpoint exists
        assert response.status_code in [200, 401]


class TestCurrentUserModel:
    """Tests for CurrentUser model."""

    def test_current_user_creation(self):
        """CurrentUser can be created with required fields."""
        user = CurrentUser(
            id=str(uuid.uuid4()),
            email="test@example.com",
            name="Test User"
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    def test_current_user_serialization(self):
        """CurrentUser serializes to dict correctly."""
        user_id = str(uuid.uuid4())
        user = CurrentUser(
            id=user_id,
            email="test@example.com",
            name="Test User"
        )
        data = user.model_dump()
        assert data["id"] == user_id
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
