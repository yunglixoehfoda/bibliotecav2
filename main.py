from database import get_connection
from models import create_tables
from datetime import datetime

from auth import login, criar_bibliotecario_padrao
from livros import (
    listar_livros,
    adicionar_livro,
    remover_livro,
    emprestar_livro, 
    atualizar_livro
)
from filtros import (
    buscar_por_filtro,
    livros_por_categoria_genero
)
from categorias import (
    listar_categorias,
    listar_generos,
    adicionar_categoria,
    adicionar_genero
)

logado = False


def menu():
    print("\n=== ACERVO DE LIVROS ===")
    print("1 - listar livros")
    print("2 - busca avançada (filtros)")
    print("3 - listar categorias")
    print("4 - listar gêneros")
    print("5 - login bibliotecário")
    print("6 - adicionar livro")
    print("7 - remover livro")
    print("8 - emprestar / devolver")
    print("9 - filtrar por categoria / gênero")
    print("10 - atualizar dados do livro")
    print("0 - sair")
    return input("opção: ")


def main():
    global logado

    conn = get_connection()
    create_tables(conn)
    criar_bibliotecario_padrao(conn)

    while True:
        opcao = menu()

        if opcao == "1":
            listar_livros(conn)

        elif opcao == "2":
            buscar_por_filtro(conn)

        elif opcao == "3":
            listar_categorias(conn, mostrar_livros=True)

        elif opcao == "4":
            listar_generos(conn, mostrar_livros=True)

        elif opcao == "5":
            if login(conn):
                logado = True

        elif opcao == "6":
            if not logado:
                print("necessário autorização.")
                continue
            adicionar_livro(conn)

        elif opcao == "7":
            if not logado:
                print("necessário autorização.")
                continue
            remover_livro(conn)

        elif opcao == "8":
            if not logado:
                print("necessário autorização.")
                continue
            emprestar_livro(conn)

        elif opcao == "9":
            livros_por_categoria_genero(conn)

        elif opcao == "10":
            if not logado:
                print("necessário autorização.")
                continue
            atualizar_livro(conn)


        elif opcao == "0":
            break

        else:
            print("opção inválida.")

    conn.close()


if __name__ == "__main__":
    main()
