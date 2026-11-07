#!/usr/bin/env python3
"""
Google OAuth Integration for ChemLab Asset Pipeline

Handles service account authentication, token refresh, and rate limiting
for Google AI Pro APIs (Gemini, Veo, Flow Music).

Requirements:
- Google Cloud Project with AI Platform API enabled
- Service account with appropriate roles
- Service account key JSON file

Usage:
    python google_oauth.py --setup           # Initial setup wizard
    python google_oauth.py --token           # Get current access token
    python google_oauth.py --refresh         # Force token refresh
    python google_oauth.py --status          # Show auth status
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    from google.auth.exceptions import GoogleAuthError
except ImportError:
    service_account = None
    Request = None
    GoogleAuthError = Exception

ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_DIR = ROOT / ".credentials"
SERVICE_ACCOUNT_FILE = CREDENTIALS_DIR / "service_account.json"
TOKEN_CACHE_FILE = CREDENTIALS_DIR / "token_cache.json"
CONFIG_FILE = CREDENTIALS_DIR / "oauth_config.json"

# Required scopes for Google AI Pro APIs
SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/generative-language",
    "https://www.googleapis.com/auth/aiplatform",
]

# Rate limiting configuration
RATE_LIMITS = {
    "gemini-2.5-flash-image": {"rpm": 60, "rpd": 1000},      # Nano Banana
    "gemini-3-pro-image-preview": {"rpm": 30, "rpd": 500},   # Nano Banana Pro
    "veo-2": {"rpm": 10, "rpd": 100},                         # Veo
    "flow-music": {"rpm": 20, "rpd": 200},                    # Flow Music/Suno
}


@dataclass
class TokenCache:
    access_token: str
    expires_at: float  # Unix timestamp
    scopes: list[str]


@dataclass
class RateLimitState:
    requests_this_minute: int = 0
    requests_today: int = 0
    minute_window_start: float = 0
    day_window_start: float = 0


@dataclass
class OAuthConfig:
    service_account_email: str = ""
    project_id: str = ""
    default_location: str = "us-central1"
    rate_limits: dict = None

    def __post_init__(self):
        if self.rate_limits is None:
            self.rate_limits = RATE_LIMITS


def ensure_credentials_dir():
    """Create credentials directory if it doesn't exist."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    # Create .gitignore to prevent committing secrets
    gitignore = CREDENTIALS_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n!README.md\n")


def load_service_account_info() -> Optional[dict]:
    """Load service account key from file."""
    if not SERVICE_ACCOUNT_FILE.exists():
        return None
    try:
        with open(SERVICE_ACCOUNT_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_token_cache() -> Optional[TokenCache]:
    """Load cached access token."""
    if not TOKEN_CACHE_FILE.exists():
        return None
    try:
        with open(TOKEN_CACHE_FILE, 'r') as f:
            data = json.load(f)
            return TokenCache(**data)
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def save_token_cache(token: TokenCache):
    """Save access token to cache."""
    ensure_credentials_dir()
    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(asdict(token), f)


def load_rate_limit_state(model: str) -> RateLimitState:
    """Load rate limit state for a model."""
    state_file = CREDENTIALS_DIR / f"rate_limit_{model.replace('.', '_').replace('-', '_')}.json"
    if not state_file.exists():
        return RateLimitState()
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
            return RateLimitState(**data)
    except (json.JSONDecodeError, OSError, TypeError):
        return RateLimitState()


def save_rate_limit_state(model: str, state: RateLimitState):
    """Save rate limit state for a model."""
    ensure_credentials_dir()
    state_file = CREDENTIALS_DIR / f"rate_limit_{model.replace('.', '_').replace('-', '_')}.json"
    with open(state_file, 'w') as f:
        json.dump(asdict(state), f)


def load_oauth_config() -> OAuthConfig:
    """Load OAuth configuration."""
    if not CONFIG_FILE.exists():
        return OAuthConfig()
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return OAuthConfig(**data)
    except (json.JSONDecodeError, OSError, TypeError):
        return OAuthConfig()


def save_oauth_config(config: OAuthConfig):
    """Save OAuth configuration."""
    ensure_credentials_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(asdict(config), f, indent=2)


def get_credentials() -> Optional[service_account.Credentials]:
    """Get Google service account credentials."""
    if service_account is None:
        print("google-auth library not installed. Run: pip install google-auth", file=sys.stderr)
        return None

    info = load_service_account_info()
    if info is None:
        print(f"Service account key not found at {SERVICE_ACCOUNT_FILE}", file=sys.stderr)
        return None

    try:
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
        return credentials
    except GoogleAuthError as e:
        print(f"Failed to create credentials: {e}", file=sys.stderr)
        return None


def get_access_token(force_refresh: bool = False) -> Optional[str]:
    """Get valid access token, refreshing if necessary."""
    credentials = get_credentials()
    if credentials is None:
        return None

    # Check cached token
    if not force_refresh:
        cached = load_token_cache()
        if cached and cached.expires_at > time.time() + 60:  # 60s buffer
            # Verify scopes match
            if set(cached.scopes) == set(SCOPES):
                return cached.access_token

    # Refresh token
    try:
        request = Request()
        credentials.refresh(request)
        token = TokenCache(
            access_token=credentials.token,
            expires_at=time.time() + 3600,  # 1 hour default
            scopes=SCOPES
        )
        save_token_cache(token)
        return credentials.token
    except GoogleAuthError as e:
        print(f"Token refresh failed: {e}", file=sys.stderr)
        return None


def check_rate_limit(model: str) -> tuple[bool, str]:
    """Check if request would exceed rate limits. Returns (allowed, message)."""
    config = load_oauth_config()
    limits = config.rate_limits.get(model, {"rpm": 60, "rpd": 1000})

    state = load_rate_limit_state(model)
    now = time.time()

    # Reset minute window if needed
    if now - state.minute_window_start >= 60:
        state.requests_this_minute = 0
        state.minute_window_start = now

    # Reset day window if needed
    if now - state.day_window_start >= 86400:
        state.requests_today = 0
        state.day_window_start = now

    # Check limits
    if state.requests_this_minute >= limits["rpm"]:
        wait = 60 - (now - state.minute_window_start)
        return False, f"Rate limit exceeded: {limits['rpm']} req/min. Wait {wait:.0f}s."

    if state.requests_today >= limits["rpd"]:
        wait = 86400 - (now - state.day_window_start)
        return False, f"Daily rate limit exceeded: {limits['rpd']} req/day. Wait {wait/3600:.1f}h."

    return True, "OK"


def record_request(model: str):
    """Record a request for rate limiting."""
    state = load_rate_limit_state(model)
    now = time.time()

    if now - state.minute_window_start >= 60:
        state.requests_this_minute = 0
        state.minute_window_start = now

    if now - state.day_window_start >= 86400:
        state.requests_today = 0
        state.day_window_start = now

    state.requests_this_minute += 1
    state.requests_today += 1
    save_rate_limit_state(model, state)


def wait_for_rate_limit(model: str, timeout: float = 300) -> bool:
    """Wait until rate limit allows a request. Returns True if allowed, False on timeout."""
    start = time.time()
    while time.time() - start < timeout:
        allowed, msg = check_rate_limit(model)
        if allowed:
            return True
        print(f"Rate limited: {msg}. Waiting...")
        time.sleep(5)
    return False


def setup_wizard():
    """Interactive setup wizard for Google OAuth."""
    print("=== Google OAuth Setup Wizard ===\n")

    print("This wizard will help you configure authentication for Google AI Pro APIs.")
    print("You need:")
    print("  1. A Google Cloud Project with AI Platform API enabled")
    print("  2. A service account with appropriate roles")
    print("  3. Service account key downloaded as JSON\n")

    # Check for existing setup
    existing = load_service_account_info()
    if existing:
        print(f"Found existing service account: {existing.get('client_email', 'unknown')}")
        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return 0

    print("\n--- Service Account Configuration ---")
    print("Paste the entire service account JSON key (end with Ctrl+D on Unix, Ctrl+Z on Windows):")

    try:
        json_input = sys.stdin.read()
        if not json_input.strip():
            print("No input provided.")
            return 1

        info = json.loads(json_input)

        # Validate required fields
        required = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id"]
        for field in required:
            if field not in info:
                print(f"Missing required field: {field}")
                return 1

        if info.get("type") != "service_account":
            print("Invalid service account type")
            return 1

        # Save service account key
        ensure_credentials_dir()
        with open(SERVICE_ACCOUNT_FILE, 'w') as f:
            json.dump(info, f, indent=2)

        # Set restrictive permissions (Unix only)
        try:
            os.chmod(SERVICE_ACCOUNT_FILE, 0o600)
        except OSError:
            pass

        print(f"\n✓ Service account saved: {info['client_email']}")

        # Save config
        config = OAuthConfig(
            service_account_email=info["client_email"],
            project_id=info["project_id"]
        )
        save_oauth_config(config)
        print(f"✓ Config saved: {CONFIG_FILE}")

        # Test authentication
        print("\n--- Testing Authentication ---")
        token = get_access_token(force_refresh=True)
        if token:
            print(f"✓ Authentication successful! Token: {token[:20]}...")
        else:
            print("✗ Authentication failed. Check service account permissions.")
            return 1

        print("\n=== Setup Complete ===")
        print(f"Credentials stored in: {CREDENTIALS_DIR}")
        print("Add this to your .gitignore:")
        print("  .credentials/")
        print("\nSet environment variable for pipeline scripts:")
        print(f"  export GOOGLE_APPLICATION_CREDENTIALS={SERVICE_ACCOUNT_FILE}")

        return 0

    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return 1
    except EOFError:
        print("\nInput cancelled.")
        return 1


def show_status():
    """Show authentication and rate limit status."""
    print("=== Google OAuth Status ===\n")

    # Service account
    info = load_service_account_info()
    if info:
        print(f"Service Account: {info.get('client_email', 'unknown')}")
        print(f"Project ID: {info.get('project_id', 'unknown')}")
    else:
        print("Service Account: NOT CONFIGURED")
        print(f"Run: python {Path(__file__).name} --setup")
        return 1

    # Token
    cached = load_token_cache()
    if cached:
        expires_in = cached.expires_at - time.time()
        if expires_in > 0:
            print(f"\nAccess Token: VALID (expires in {expires_in/60:.1f} min)")
        else:
            print(f"\nAccess Token: EXPIRED (will auto-refresh)")
    else:
        print(f"\nAccess Token: NOT CACHED (will fetch on first use)")

    # Test fresh token
    token = get_access_token()
    if token:
        print(f"Token Fetch: SUCCESS")
    else:
        print(f"Token Fetch: FAILED")

    # Rate limits
    config = load_oauth_config()
    print(f"\n--- Rate Limits ---")
    for model, limits in config.rate_limits.items():
        state = load_rate_limit_state(model)
        print(f"  {model}:")
        print(f"    Minute: {state.requests_this_minute}/{limits['rpm']} "
              f"({60 - (time.time() - state.minute_window_start):.0f}s reset)")
        print(f"    Day: {state.requests_today}/{limits['rpd']} "
              f"({(86400 - (time.time() - state.day_window_start))/3600:.1f}h reset)")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Google OAuth Integration for ChemLab Asset Pipeline")
    parser.add_argument("--setup", action="store_true", help="Run interactive setup wizard")
    parser.add_argument("--token", action="store_true", help="Get current access token")
    parser.add_argument("--refresh", action="store_true", help="Force token refresh")
    parser.add_argument("--status", action="store_true", help="Show auth and rate limit status")
    parser.add_argument("--check-rate-limit", metavar="MODEL", help="Check rate limit for model")
    parser.add_argument("--wait-rate-limit", metavar="MODEL", help="Wait for rate limit to allow request")
    args = parser.parse_args()

    if args.setup:
        return setup_wizard()

    if args.token:
        token = get_access_token(force_refresh=args.refresh)
        if token:
            print(token)
            return 0
        else:
            print("Failed to get token", file=sys.stderr)
            return 1

    if args.refresh:
        token = get_access_token(force_refresh=True)
        if token:
            print("Token refreshed successfully")
            return 0
        else:
            print("Token refresh failed", file=sys.stderr)
            return 1

    if args.status:
        return show_status()

    if args.check_rate_limit:
        allowed, msg = check_rate_limit(args.check_rate_limit)
        print(f"Allowed: {allowed} - {msg}")
        return 0 if allowed else 1

    if args.wait_rate_limit:
        if wait_for_rate_limit(args.wait_rate_limit):
            print("Rate limit OK - request allowed")
            return 0
        else:
            print("Timeout waiting for rate limit", file=sys.stderr)
            return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())