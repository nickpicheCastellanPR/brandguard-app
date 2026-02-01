import hashlib
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Initialize Argon2 hasher with secure defaults
ph = PasswordHasher(
    time_cost=2,        # number of iterations
    memory_cost=65536,  # 64 MB
    parallelism=2,      # number of parallel threads
    hash_len=32,        # length of hash in bytes
    salt_len=16         # length of salt in bytes
)

def hash_password(password: str) -> str:
    """
    Hash password using Argon2.
    Returns format: "argon2:hash" where hash is from Argon2's output.

    Argon2 PasswordHasher.hash() returns a full encoded string with all parameters,
    prefix it to mark it as argon2. Useful if we need to upgrade to a new hash function later.
    """
    argon2_hash = ph.hash(password)
    # Argon2 is cool. The hash contains all info: $argon2id$v=19$m=65536,t=2,p=2$...$...
    return f"argon2:{argon2_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify password against stored hash.
    Handles both legacy SHA256 and new Argon2 formats.

    Args:
        password: Plain text password from user
        stored_hash: Hash from database (either "argon2:..." or legacy SHA256)

    Returns:
        True if password matches, False otherwise
    """
    # Check if this is a new-format password (contains our prefix)
    if stored_hash.startswith("argon2:"):
        # Remove the prefix to get the actual hash
        argon2_hash = stored_hash[7:]

        try:
            # Argon2 verify throws exception if password doesn't match
            ph.verify(argon2_hash, password)
            return True
        except VerifyMismatchError:
            return False
        except Exception as e:
            # Handle any other Argon2 errors (corrupted hash, etc.)
            print(f"Argon2 verification error: {e}")
            return False

    else:
        # Legacy SHA256 format (no colons, just hex string)
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        return secrets.compare_digest(legacy_hash, stored_hash)


def should_rehash_password(stored_hash: str) -> bool:
    """
    Check if a stored password should be rehashed.

    Returns True if:
    - It's a legacy SHA256 hash (no "argon2:" prefix)
    - It's an Argon2 hash but parameters are outdated

    This allows gradual migration of all passwords to current best practices.
    """
    if not stored_hash.startswith("argon2:"):
        # Legacy SHA256 - should definitely be upgraded
        return True

    # For Argon2 hashes, check if parameters need updating
    argon2_hash = stored_hash[7:]
    try:
        # check_needs_rehash returns True if params have changed
        return ph.check_needs_rehash(argon2_hash)
    except:
        # If we can't parse it, play it safe and don't rehash
        return False


def upgrade_password_on_login(username: str, password: str, stored_hash: str, save_callback):
    """
    Helper to upgrade legacy passwords to Argon2 on successful login.

    Args:
        username: User's username
        password: Plain text password (just verified as correct)
        stored_hash: Current hash from database
        save_callback: Function to save new hash to database
                      Should accept (username, new_hash) and return bool

    Returns:
        True if upgrade was needed and succeeded, False otherwise
    """
    if should_rehash_password(stored_hash):
        new_hash = hash_password(password)
        try:
            return save_callback(username, new_hash)
        except Exception as e:
            print(f"Password upgrade failed for {username}: {e}")
            # Don't fail the login just because upgrade failed
            return False
    return False
