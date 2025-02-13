import os
from openai import OpenAI
from flask import current_app
import re

def init_openai():
    """
    Inicializa a chave da API da OpenAI a partir das configurações da aplicação.
    """
    print("Inicializando OpenAI...")

def limpar_query(query):
    """
    Remove blocos de código Markdown da query, se presentes.
    
    Args:
        query (str): A query SQL gerada pelo modelo.
    
    Returns:
        str: A query SQL limpa.
    """
    # Remove ```sql no início e ``` no fim
    query = re.sub(r'^```sql\s*', '', query, flags=re.IGNORECASE)
    query = re.sub(r'\s*```$', '', query, flags=re.IGNORECASE)

    # Remove quaisquer outras marcações de bloco de código
    query = re.sub(r'^```.*\n', '', query, flags=re.MULTILINE)
    query = re.sub(r'\n```$', '', query, flags=re.MULTILINE)

    # Remove qualquer outra formatação de bloco de código
    query = query.replace('```', '').strip()

    return query

def traduzir_para_query(schema, pergunta):
    """
    Converte uma pergunta em linguagem natural para uma query SQL utilizando a API da OpenAI.
    Para CADA interação com um humano, VOCÊ DEVE SEMPRE primeiro se envolver em um processo de pensamento *abrangente, natural e não filtrado* antes de responder.
    Além disso, VOCÊ também é capaz de pensar e refletir durante a resposta quando considera necessário.

    Args:
        schema (str): O schema do banco de dados em texto.
        pergunta (str): A pergunta em linguagem natural.

    Returns:
        str: A query SQL gerada ou uma mensagem de erro.
    """
    prompt = f"""
    Para CADA interação com um humano, VOCÊ DEVE SEMPRE primeiro se envolver em um processo de pensamento *abrangente, natural e não filtrado* antes de responder.
    Além disso, VOCÊ também é capaz de pensar e refletir durante a resposta quando considera necessário.
    Você é um assistente que converte perguntas em linguagem natural para queries SQL do MySQL, usando o seguinte schema do banco de dados:
    É MUITO IMPORTANTE QUE VOCÊ ENTENDA O SCHEMA DAS TABELAS ANTES DE GERAR A CONSULTA!

    {schema}

    Retorne apenas a query SQL sem qualquer formatação adicional ou blocos de código.
    """

    try:
        client = OpenAI( api_key = current_app.config['OPENAI_API_KEY'])
        # Utilizando a interface atualizada da API ChatCompletion
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # ou outro modelo disponível
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""Pergunta: {pergunta}"""},
            ],
            temperature=0,  # Para respostas mais determinísticas
        )

        # Extrair apenas o conteúdo da mensagem
        query = response.choices[0].message.content

        # Limpar a query de quaisquer blocos de código Markdown
        query = limpar_query(query)

        # Validação simples: Garantir que a query começa com SELECT
        if not re.match(r'^SELECT', query, re.IGNORECASE):
            raise ValueError("A query gerada não é uma SELECT. Somente queries SELECT são permitidas.")

        return query
    except Exception as e:
        current_app.logger.error(f"Erro na tradução para query: {e}")
        return f"Erro na tradução da pergunta: {str(e)}"