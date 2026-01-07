"""
Authentication Service.

Handles user authentication, registration, and session management.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import uuid
import hashlib
import secrets

from alfred.core.services.base import BaseService


class AuthService(BaseService):
    """
    Authentication and user management service.

    Handles:
    - User registration
    - Login/authentication
    - Password hashing
    - Token generation
    """

    def __init__(
        self,
        storage: Any = None,
        secret_key: str = "default-secret-key",
        token_expiry_hours: int = 24 * 7,  # 1 week
        **kwargs,
    ):
        super().__init__(storage=storage, **kwargs)
        self.secret_key = secret_key
        self.token_expiry_hours = token_expiry_hours

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        try:
            import bcrypt
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode(), salt).decode()
        except ImportError:
            # Fallback to SHA256 if bcrypt not available
            return hashlib.sha256(
                (password + self.secret_key).encode()
            ).hexdigest()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except ImportError:
            # Fallback verification
            return self.hash_password(password) == hashed

    def generate_token(self, user_id: str) -> Tuple[str, datetime]:
        """
        Generate an access token for a user.

        Returns:
            Tuple of (token, expiry_datetime)
        """
        try:
            from jose import jwt
            expiry = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            payload = {
                "sub": user_id,
                "exp": expiry,
                "iat": datetime.utcnow(),
                "jti": str(uuid.uuid4()),
            }
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            return token, expiry
        except ImportError:
            # Simple token fallback
            token = f"{user_id}:{secrets.token_urlsafe(32)}"
            expiry = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            return token, expiry

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify a token and return user_id if valid.

        Returns:
            user_id if valid, None otherwise
        """
        try:
            from jose import jwt, JWTError
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload.get("sub")
        except ImportError:
            # Simple token fallback
            if ":" in token:
                return token.split(":")[0]
            return None
        except Exception:
            return None

    async def register(
        self,
        email: str,
        password: str,
        name: str,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Register a new user.

        Args:
            email: User's email
            password: Plain text password
            name: User's display name
            preferences: Optional initial preferences

        Returns:
            Tuple of (user_id, error_message)
        """
        self._ensure_storage()

        # Check if user exists
        existing = self.storage.get_user_credentials(email)
        if existing:
            return None, "Email already registered"

        # Create user
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)

        success = self.storage.create_user(
            user_id=user_id,
            email=email,
            password_hash=password_hash,
        )

        if not success:
            return None, "Failed to create user"

        # Update profile with name and preferences
        profile_data = {"name": name}
        if preferences:
            profile_data["preferences"] = preferences

        self.storage.update_user_profile(user_id, profile_data)

        self._log_action("REGISTER", user_id, f"email={email}")
        return user_id, None

    async def login(
        self,
        email: str,
        password: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate a user.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            Tuple of (auth_data, error_message)
            auth_data contains: user_id, token, expiry
        """
        self._ensure_storage()

        # Get user credentials
        credentials = self.storage.get_user_credentials(email)
        if not credentials:
            return None, "Invalid email or password"

        # Verify password
        if not self.verify_password(password, credentials["password_hash"]):
            return None, "Invalid email or password"

        user_id = credentials["user_id"]

        # Generate token
        token, expiry = self.generate_token(user_id)

        # Get user profile
        profile = self.storage.get_user_profile(user_id) or {}

        self._log_action("LOGIN", user_id, f"email={email}")

        return {
            "user_id": user_id,
            "token": token,
            "expiry": expiry.isoformat(),
            "user": {
                "id": user_id,
                "email": email,
                "name": profile.get("name", ""),
            },
        }, None

    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get current user from token.

        Args:
            token: Access token

        Returns:
            User data if valid, None otherwise
        """
        user_id = self.verify_token(token)
        if not user_id:
            return None

        self._ensure_storage()
        return self.storage.get_user_profile(user_id)

    async def update_profile(
        self,
        user_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update user profile."""
        self._ensure_storage()

        success = self.storage.update_user_profile(user_id, updates)
        if success:
            self._log_action("UPDATE_PROFILE", user_id)
        return success
