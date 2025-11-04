from cryptography.hazmat.primitives.asymmetric import ec
from base64 import urlsafe_b64encode

def b64url_no_pad(b: bytes) -> str:
    return urlsafe_b64encode(b).decode("utf-8").rstrip("=")

# generate P-256 keypair (this is what VAPID expects)
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# --- private key (32 bytes) ---
priv_num = private_key.private_numbers().private_value
priv_bytes = priv_num.to_bytes(32, "big")

# --- public key (uncompressed: 0x04 || x || y) ---
pub_nums = public_key.public_numbers()
x = pub_nums.x.to_bytes(32, "big")
y = pub_nums.y.to_bytes(32, "big")
public_key_uncompressed = b"\x04" + x + y  # 65 bytes

print("VAPID_PRIVATE_KEY=", b64url_no_pad(priv_bytes))
print("VAPID_PUBLIC_KEY=", b64url_no_pad(public_key_uncompressed))
