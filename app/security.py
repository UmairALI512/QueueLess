import hashlib,hmac,secrets
def make_hash(password):
    salt=secrets.token_hex(16)
    digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),310000).hex()
    return f"{salt}${digest}"
def check(password,stored):
    try:
        salt,digest=stored.split("$",1)
        actual=hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),310000).hex()
        return hmac.compare_digest(actual,digest)
    except Exception: return False
