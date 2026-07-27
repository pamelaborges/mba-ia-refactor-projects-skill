CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


def validar_produto(dados):
    if "nome" not in dados:
        return ["Nome é obrigatório"]
    if "preco" not in dados:
        return ["Preço é obrigatório"]
    if "estoque" not in dados:
        return ["Estoque é obrigatório"]

    erros = []
    if dados["preco"] < 0:
        erros.append("Preço não pode ser negativo")
    if dados["estoque"] < 0:
        erros.append("Estoque não pode ser negativo")
    if len(dados["nome"]) < 2:
        erros.append("Nome muito curto")
    if len(dados["nome"]) > 200:
        erros.append("Nome muito longo")

    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        erros.append("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return erros
