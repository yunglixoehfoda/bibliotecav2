from flask import Flask, render_template, request, redirect, jsonify
from database import get_connection
from models import create_tables
from livros import listar_livros, adicionar_livro, buscar_livros
from livros import emprestar_livro, devolver_livro
from livros import buscar_livro_por_id, atualizar_livro
from livros import remover_livro
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from functools import wraps
from werkzeug.security import check_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file
from datetime import datetime, date
from datetime import timedelta



app = Flask(__name__)
app.secret_key = "jokerehfoda"



PRAZO_DIAS = 7  # por exemplo, 7 dias de prazo

def preparar_livros(livros):
    """
    Recebe lista de livros do banco (dicionários ou objetos)
    e adiciona campos:
      - dias_emprestimo
      - alerta (True/False)
      - data_emprestimo_formatada
    """
    hoje = date.today()

    for l in livros:
        if l['disponivel']:
            l['dias_emprestimo'] = 0
            l['alerta'] = False
            l['data_emprestimo_formatada'] = None
        else:
            if l['data_emprestimo']:
                data_emp = datetime.strptime(l['data_emprestimo'], "%Y-%m-%d").date()
                l['dias_emprestimo'] = (hoje - data_emp).days
                l['alerta'] = l['dias_emprestimo'] > PRAZO_DIAS
                l['data_emprestimo_formatada'] = data_emp.strftime("%d/%m/%Y")
            else:
                l['dias_emprestimo'] = 0
                l['alerta'] = False
                l['data_emprestimo_formatada'] = None
    return livros
def preparar_livros_home(livros):
    hoje = date.today()
    livros_ok = []

    for l in livros:
        livro = dict(l)

        if livro["disponivel"]:
            livro["dias_emprestimo"] = 0
            livro["prazo_total"] = 0
        else:
            # busca empréstimo ativo
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT data_emprestimo, data_limite
                FROM loans
                WHERE book_id = ? AND data_devolucao IS NULL
            """, (livro["id"],))
            emp = cur.fetchone()
            conn.close()

            if emp:
                data_emp = datetime.strptime(emp["data_emprestimo"], "%Y-%m-%d").date()
                livro["dias_emprestimo"] = (hoje - data_emp).days
                livro["prazo_total"] = (
                    datetime.strptime(emp["data_limite"], "%Y-%m-%d").date()
                    - data_emp
                ).days
            else:
                livro["dias_emprestimo"] = 0
                livro["prazo_total"] = 0

        livros_ok.append(livro)

    return livros_ok

def bibliotecario_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_role" not in session or session["user_role"] != "bibliotecario":
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def get_db():
    conn = sqlite3.connect("acervo.db")
    conn.row_factory = sqlite3.Row
    return conn

db_ok = False
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM users
            WHERE username = ?
        """, (username,))

        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect("/livros")

        return render_template("login.html", erro="Usuário ou senha incorretos")

    return render_template("login.html")


    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
def login_required():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect("/login")
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.before_request
def init_db():
    global db_ok
    if not db_ok:
        conn = get_connection()
        create_tables(conn)
        conn.close()
        db_ok = True


@app.route("/")
def index():
    conn = get_connection()

    termo = request.args.get("q")
    categoria = request.args.get("categoria")
    genero = request.args.get("genero")

    livros = buscar_livros(conn, termo, categoria, genero)
    conn.close()

    livros = preparar_livros_home(livros)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM categories")
    categorias = cur.fetchall()

    cur.execute("SELECT id, nome FROM genres")
    generos = cur.fetchall()
    conn.close()

    return render_template(
        "index.html",
        livros=livros,
        categorias=categorias,
        generos=generos,
        prazo_padrao=8
    )




@app.route("/livros")
@login_required()
def livros():
    conn = get_db()
    cur = conn.cursor()

    q = request.args.get("q", "").strip()
    categoria = request.args.get("categoria")
    genero = request.args.get("genero")

    # =========================
    # BUSCA DOS LIVROS
    # =========================
    sql = """
        SELECT
            b.id,
            b.titulo,
            b.autor,
            b.ano,
            b.isbn,
            b.idioma,
            b.disponivel,
            c.nome AS categoria,
            g.nome AS genero
        FROM books b
        LEFT JOIN categories c ON b.categoria_id = c.id
        LEFT JOIN genres g ON b.genero_id = g.id
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND (b.titulo LIKE ? OR b.autor LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])

    if categoria:
        sql += " AND b.categoria_id = ?"
        params.append(categoria)

    if genero:
        sql += " AND b.genero_id = ?"
        params.append(genero)

    cur.execute(sql, params)
    livros = cur.fetchall()

    # =========================
    # BUSCA DOS EMPRÉSTIMOS ATIVOS
    # =========================
    cur.execute("""
        SELECT
            l.id AS loan_id,
            l.book_id,
            l.nome,
            l.serie,
            l.turma,
            l.tipo_livro,
            l.data_emprestimo,
            l.data_limite,
            julianday('now') - julianday(l.data_emprestimo) AS dias_passados,
            julianday(l.data_limite) - julianday(l.data_emprestimo) AS prazo_total
        FROM loans l
        WHERE l.data_devolucao IS NULL
    """)
    emprestimos = cur.fetchall()

    # =========================
    # FORMATAR DADOS
    # =========================
    livros_formatados = []
    hoje = date.today()

    for l in livros:
        livro = dict(l)

        # procura empréstimo desse livro
        emp = next(
            (dict(e) for e in emprestimos if e["book_id"] == livro["id"]),
            None
        )

        if emp:
            data_emp = datetime.strptime(emp["data_emprestimo"], "%Y-%m-%d").date()

            livro["emprestado"] = True
            livro["loan_id"] = emp["loan_id"]
            livro["emprestado_para"] = f'{emp["nome"]} — {emp["serie"]}{emp["turma"]}'
            livro["data_emprestimo_formatada"] = data_emp.strftime("%d/%m/%Y")
            livro["dias_emprestimo"] = (hoje - data_emp).days
            livro["prazo_total"] = int(emp["prazo_total"])
            livro["alerta"] = livro["dias_emprestimo"] > livro["prazo_total"]
        else:
            livro["emprestado"] = False
            livro["loan_id"] = None
            livro["emprestado_para"] = ""
            livro["data_emprestimo_formatada"] = ""
            livro["dias_emprestimo"] = 0
            livro["prazo_total"] = 0
            livro["alerta"] = False

        livros_formatados.append(livro)

    # =========================
    # FILTROS
    # =========================
    cur.execute("SELECT id, nome FROM categories")
    categorias = cur.fetchall()

    cur.execute("SELECT id, nome FROM genres")
    generos = cur.fetchall()

    conn.close()

    return render_template(
        "livros.html",
        livros=livros_formatados,
        categorias=categorias,
        generos=generos
    )



@app.route("/livro/novo", methods=["GET", "POST"])
@login_required()
def livro_novo():
    conn = get_connection()

    if request.method == "POST":
        adicionar_livro(
            conn,
            request.form["titulo"],
            request.form["autor"],
            request.form["ano"],
            request.form["isbn"],
            request.form["idioma"],
            request.form["categoria"],
            request.form["genero"]
        )
        conn.close()
        return redirect("/livros")

    cur = conn.cursor()
    cur.execute("SELECT nome FROM categories")
    categorias = cur.fetchall()

    cur.execute("SELECT nome FROM genres")
    generos = cur.fetchall()

    conn.close()

    return render_template(
        "livro_novo.html",
        categorias=categorias,
        generos=generos
    )




@app.route("/livro/<int:id>/emprestar", methods=["POST"])
@app.route("/livro/<int:id>/emprestar", methods=["POST"])
def emprestar(id):
    nome = request.form["nome"]
    serie = request.form["serie"]
    turma = request.form["turma"]
    tipo = request.form["tipo_livro"]  # fino | grosso

    prazo = 8 if tipo == "fino" else 20

    hoje = date.today()
    data_limite = hoje + timedelta(days=prazo)

    conn = get_db()
    cur = conn.cursor()

    # cria empréstimo
    cur.execute("""
        INSERT INTO loans
        (book_id, nome, serie, turma, tipo_livro, data_emprestimo, data_limite)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        id,
        nome,
        serie,
        turma,
        tipo,
        hoje.isoformat(),
        data_limite.isoformat()
    ))

    # marca livro indisponível
    cur.execute("UPDATE books SET disponivel=0 WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})



@app.route("/loan/<int:loan_id>/devolver", methods=["POST"])
@login_required()
def devolver_loan(loan_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE loans
        SET data_devolucao = DATE('now')
        WHERE id = ?
    """, (loan_id,))

    cur.execute("""
        UPDATE books
        SET disponivel = 1
        WHERE id = (
            SELECT book_id FROM loans WHERE id = ?
        )
    """, (loan_id,))

    conn.commit()
    conn.close()

    return {"ok": True}



@app.route("/livro/<int:id>/editar", methods=["GET", "POST"])
@login_required()
def editar_livro(id):
    conn = get_connection()

    if request.method == "POST":
        atualizar_livro(
            conn,
            id,
            request.form["titulo"],
            request.form["autor"],
            request.form["ano"],
            request.form["isbn"],
            request.form["idioma"],
            request.form["categoria"],
            request.form["genero"]
        )
        conn.close()
        return redirect("/livros")

    livro = buscar_livro_por_id(conn, id)

    cur = conn.cursor()
    cur.execute("SELECT nome FROM categories")
    categorias = cur.fetchall()

    cur.execute("SELECT nome FROM genres")
    generos = cur.fetchall()

    conn.close()

    return render_template(
        "livro_editar.html",
        livro=livro,
        categorias=categorias,
        generos=generos
    )


@app.route("/livro/<int:id>/remover", methods=["POST"])
def remover(id):
    conn = get_connection()
    remover_livro(conn, id)
    conn.close()
    return redirect("/livros")


@app.route("/backup/livros")
def backup_livros():
    conn = get_db()
    cur = conn.cursor()

    # pega todos os livros com categorias e gêneros
    cur.execute("""
        SELECT b.titulo, b.autor, b.ano, b.isbn, b.idioma,
               c.nome AS categoria, g.nome AS genero
        FROM books b
        LEFT JOIN categories c ON b.categoria_id = c.id
        LEFT JOIN genres g ON b.genero_id = g.id
    """)
    livros = cur.fetchall()
    conn.close()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ================================
    # Página 1: Lista de livros legível
    # ================================
    y = height - 40
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Backup de Livros - Lista")
    y -= 30

    pdf.setFont("Helvetica", 11)
    for l in livros:
        linhas = [
            f"Título: {l['titulo']}",
            f"Autor: {l['autor']}",
            f"Ano: {l['ano'] or '-'}",
            f"ISBN: {l['isbn'] or '-'}",
            f"Idioma: {l['idioma']}",
            f"Categoria: {l['categoria'] or '-'}",
            f"Gênero: {l['genero'] or '-'}",
            "-" * 80
        ]
        for linha in linhas:
            if y < 40:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = height - 40
            pdf.drawString(40, y, linha)
            y -= 14

    # ================================
    # Página 2: Código Python pronto
    # ================================
    pdf.showPage()
    pdf.setFont("Courier-Bold", 14)
    pdf.drawString(40, height - 40, "meu quebra galho pra restaurar livros")
    y = height - 60
    pdf.setFont("Courier", 10)

    python_lines = [
        "from database import get_connection",
        "",
        "livros = ["
    ]

    # adiciona os livros no formato do código
    for l in livros:
        linha = f"    ('{l['titulo']}', '{l['autor']}', {l['ano'] or 0}, '{l['isbn'] or '0'}', '{l['idioma']}', '{l['categoria'] or ''}', '{l['genero'] or ''}'),"
        python_lines.append(linha)
    python_lines.append("]")
    python_lines += [
        "",
        "conn = get_connection()",
        "cur = conn.cursor()",
        "",
        "for l in livros:",
        "    cur.execute(\"\"\"",
        "        INSERT INTO books",
        "        (titulo, autor, ano, isbn, idioma, categoria_id, genero_id)",
        "        VALUES (?, ?, ?, ?, ?,",
        "                (SELECT id FROM categories WHERE nome=?),",
        "                (SELECT id FROM genres WHERE nome=?))",
        "    \"\"\", l)",
        "",
        "conn.commit()",
        "conn.close()",
        "",
        "print('livros restaurados com sucesso!')"
    ]

    # escreve cada linha no PDF
    for pl in python_lines:
        if y < 40:
            pdf.showPage()
            pdf.setFont("Courier", 10)
            y = height - 40
        pdf.drawString(40, y, pl)
        y -= 12

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="backup_livros.pdf",
        mimetype="application/pdf"
    )

@app.route("/devolver/<int:loan_id>")
@login_required()
def devolver(loan_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE loans
        SET data_devolucao = DATE('now')
        WHERE id = ?
    """, (loan_id,))

    cur.execute("""
        UPDATE books
        SET disponivel = 1
        WHERE id = (
            SELECT book_id FROM loans WHERE id = ?
        )
    """, (loan_id,))

    conn.commit()
    conn.close()

    return redirect("/livros")



if __name__ == "__main__":
    app.run(debug=True)
