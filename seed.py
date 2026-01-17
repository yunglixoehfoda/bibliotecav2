from database import get_connection

categorias = [
    "Literatura",
    "Fantasia",
    "Romance",
    "Ficção",
    "Fantasia",
    "Suspense",
    "Terror",
    "Drama",
    "Poesia",
    "Biografia",
    "História",
    "Ciência"
]

generos = [
    "Modernismo Brasileiro",
    "Técnico",
    "Clássico",
    "Contemporâneo",
    "Juvenil",
    "Infantil",
    "Acadêmico",
    "Religioso",
    "HQ",
    "Mangá"
]

conn = get_connection()
cur = conn.cursor()

for c in categorias:
    cur.execute("INSERT OR IGNORE INTO categories (nome) VALUES (?)", (c,))

for g in generos:
    cur.execute("INSERT OR IGNORE INTO genres (nome) VALUES (?)", (g,))

conn.commit()
conn.close()

print("categorias e gêneros inseridos")
