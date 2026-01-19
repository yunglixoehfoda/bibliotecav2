def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        autor TEXT NOT NULL,
        ano INTEGER,
        isbn TEXT,
        categoria_id INTEGER,
        genero_id INTEGER,
        idioma TEXT,
        disponivel INTEGER DEFAULT 1,
        emprestado_para TEXT,
        data_emprestimo TEXT,
        FOREIGN KEY (categoria_id) REFERENCES categories(id),
        FOREIGN KEY (genero_id) REFERENCES genres(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        serie TEXT NOT NULL,
        turma TEXT NOT NULL CHECK (turma IN ('A','B','C','D','E')),
        tipo_livro TEXT NOT NULL CHECK (tipo_livro IN ('fino','grosso')),
        data_emprestimo DATE NOT NULL,
        data_limite DATE NOT NULL,
        data_devolucao DATE,
        FOREIGN KEY (book_id) REFERENCES books(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    conn.commit()


