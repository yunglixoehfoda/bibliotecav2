from database import get_connection

conn = get_connection()
cur = conn.cursor()

# apaga todos os usuários
cur.execute("DELETE FROM users")

conn.commit()
conn.close()

print("tabela users zerada")
