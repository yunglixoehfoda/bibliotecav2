from database import get_connection
from werkzeug.security import generate_password_hash

usuario = {
    "username": "betyseba",
    "password": generate_password_hash("2dsadas"),
    "role": "admin"
}

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    INSERT INTO users (username, password, role)
    VALUES (?, ?, ?)
""", (usuario["username"], usuario["password"], usuario["role"]))

conn.commit()
conn.close()

print("usuário admin criado com senha hash")
