import secrets

# No 0/O nor 1/I, so a code read aloud or copied by hand is not mistyped.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6


class SecureDice:
    def roll(self, faces: int) -> int:
        return secrets.randbelow(faces) + 1


class SecureCodeGenerator:
    def new_code(self) -> str:
        return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


class SecureTokenGenerator:
    def new_token(self) -> str:
        return secrets.token_urlsafe(32)
