def dados_para_tabela_html(dados):
    """
    Converte uma lista de dicionários em uma tabela HTML simples.

    Args:
        dados (list of dict): Os resultados da query, onde cada dicionário representa uma linha.

    Returns:
        str: Uma string contendo a tabela HTML.
    """
    if not dados:
        return "<p>Nenhum dado encontrado.</p>"

    # Extrair os cabeçalhos da tabela a partir das chaves do primeiro dicionário
    headers = dados[0].keys()

    # Iniciar a tabela HTML com borda simples
    tabela_html = "<table border='1' cellspacing='0' cellpadding='5'>"

    # Adicionar os cabeçalhos
    tabela_html += "<tr>"
    for header in headers:
        tabela_html += f"<th>{header.capitalize()}</th>"
    tabela_html += "</tr>"

    # Adicionar as linhas de dados
    for linha in dados:
        tabela_html += "<tr>"
        for header in headers:
            valor = linha.get(header, "")
            tabela_html += f"<td>{valor}</td>"
        tabela_html += "</tr>"

    # Fechar a tabela
    tabela_html += "</table>"

    return tabela_html