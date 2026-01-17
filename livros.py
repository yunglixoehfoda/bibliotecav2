from datetime import date

def emprestar_livro(conn, livro_id, nome_pessoa):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE books
        SET
            disponivel = 0,
            emprestado_para = ?,
            data_emprestimo = ?
        WHERE id = ?
    """, (nome_pessoa, date.today().isoformat(), livro_id))
    conn.commit()

def devolver_livro(conn, livro_id):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE books
        SET
            disponivel = 1,
            emprestado_para = NULL,
            data_emprestimo = NULL
        WHERE id = ?
    """, (livro_id,))
    conn.commit()









def listar_livros(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            b.id,
            b.titulo,
            b.autor,
            c.nome AS categoria,
            g.nome AS genero,
            b.idioma,
            b.disponivel,
            b.emprestado_para
        FROM books b
        LEFT JOIN categories c ON b.categoria_id = c.id
        LEFT JOIN genres g ON b.genero_id = g.id
    """)
    return cursor.fetchall()



def adicionar_livro(
    conn, titulo, autor, ano, isbn,
    idioma, categoria_nome, genero_nome
):
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO categories (nome) VALUES (?)", (categoria_nome,))
    cursor.execute("SELECT id FROM categories WHERE nome = ?", (categoria_nome,))
    categoria_id = cursor.fetchone()["id"]

    cursor.execute("INSERT OR IGNORE INTO genres (nome) VALUES (?)", (genero_nome,))
    cursor.execute("SELECT id FROM genres WHERE nome = ?", (genero_nome,))
    genero_id = cursor.fetchone()["id"]

    cursor.execute("""
        INSERT INTO books (
            titulo, autor, ano, isbn,
            categoria_id, genero_id, idioma
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        titulo, autor, ano, isbn,
        categoria_id, genero_id, idioma
    ))

    conn.commit()

def buscar_livros(conn, termo=None, categoria=None, genero=None):
    cursor = conn.cursor()

    query = """
        SELECT
            b.id,
            b.titulo,
            b.autor,
            c.nome AS categoria,
            g.nome AS genero,
            b.idioma,
            b.disponivel,
            b.emprestado_para
        FROM books b
        LEFT JOIN categories c ON b.categoria_id = c.id
        LEFT JOIN genres g ON b.genero_id = g.id
        WHERE 1=1
    """

    params = []

    if termo:
        query += " AND (b.titulo LIKE ? OR b.autor LIKE ?)"
        params.append(f"%{termo}%")
        params.append(f"%{termo}%")

    if categoria:
        query += " AND b.categoria_id = ?"
        params.append(categoria)

    if genero:
        query += " AND b.genero_id = ?"
        params.append(genero)

    cursor.execute(query, params)
    return cursor.fetchall()



def buscar_livro_por_id(conn, livro_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            b.id,
            b.titulo,
            b.autor,
            b.ano,
            b.isbn,
            b.idioma,
            c.nome AS categoria,
            g.nome AS genero
        FROM books b
        LEFT JOIN categories c ON b.categoria_id = c.id
        LEFT JOIN genres g ON b.genero_id = g.id
        WHERE b.id = ?
    """, (livro_id,))
    return cursor.fetchone()




def atualizar_livro(
    conn, livro_id, titulo, autor, ano, isbn, idioma, categoria, genero
):
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO categories (nome) VALUES (?)", (categoria,))
    cursor.execute("SELECT id FROM categories WHERE nome = ?", (categoria,))
    categoria_id = cursor.fetchone()["id"]

    cursor.execute("INSERT OR IGNORE INTO genres (nome) VALUES (?)", (genero,))
    cursor.execute("SELECT id FROM genres WHERE nome = ?", (genero,))
    genero_id = cursor.fetchone()["id"]

    cursor.execute("""
        UPDATE books
        SET
            titulo = ?,
            autor = ?,
            ano = ?,
            isbn = ?,
            idioma = ?,
            categoria_id = ?,
            genero_id = ?
        WHERE id = ?
    """, (
        titulo, autor, ano, isbn, idioma,
        categoria_id, genero_id, livro_id
    ))

    conn.commit()

def remover_livro(conn, livro_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (livro_id,))
    conn.commit()

