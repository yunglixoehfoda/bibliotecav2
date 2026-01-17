from security import hash_password, verify_password

def criar_bibliotecario_padrao(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE role = 'librarian'")
    if cursor.fetchone():
        return

    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        ("admin", hash_password("admin123"), "librarian")
    )
    conn.commit()


def autenticar_usuario(conn, username: str, password: str):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password, role FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()

    if not user:
        return None

    user_id, user_name, password_hash, role = user

    if not verify_password(password, password_hash):
        return None

    return {
        "id": user_id,
        "username": user_name,
        "role": role
    }
