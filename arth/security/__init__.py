"""ARTH Security Package.
Implements Sections 12, 30, and 31 of ARTH_SPEC:
- Voice lock verification
- Salted password management with 5-minute lockout after 3 failed attempts
- Local offline face verification with anti-spoofing challenge
- Lockdown controller to freeze ARTH and lock display
"""

from arth.security.auth import SecurityManager
from arth.security.lockdown import LockdownController

__all__ = ["SecurityManager", "LockdownController"]
