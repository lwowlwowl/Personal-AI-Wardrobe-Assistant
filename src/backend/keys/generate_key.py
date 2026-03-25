from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import os

# 创建目录
os.makedirs("D:/keys", exist_ok=True)

# 生成私钥
private_key = ed25519.Ed25519PrivateKey.generate()

# 保存私钥
with open("D:/keys/qweather_private.pem", "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

# 生成公钥
public_key = private_key.public_key()

# 保存公钥
with open("D:/keys/qweather_public.pem", "wb") as f:
    f.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

print("密钥生成完成！")
print("私钥路径: D:/keys/qweather_private.pem")
print("公钥路径: D:/keys/qweather_public.pem")