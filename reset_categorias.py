from database import get_connection

conn = get_connection()
cur = conn.cursor()

# 1️⃣ remove vínculos dos livros
cur.execute("""
    UPDATE books
    SET categoria_id = NULL,
        genero_id = NULL
""")

# 2️⃣ apaga categorias e gêneros
cur.execute("DELETE FROM categories")
cur.execute("DELETE FROM genres")

conn.commit()
conn.close()

print("categorias e gêneros zerados, livros preservados")
