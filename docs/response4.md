Entendi o problema. O erro ocorre porque a query SQL gerada está sendo retornada com a formatação de bloco de código Markdown (````sql` e ```), o que causa uma sintaxe inválida no MySQL. Precisamos garantir que a query SQL seja extraída **apenas** sem quaisquer formatações adicionais.

Vamos ajustar tanto o **prompt** enviado para o modelo da OpenAI quanto o **código** que processa a resposta para remover qualquer formatação indesejada.

## **Passo 1: Ajustar o Prompt para Evitar Formatações de Bloco de Código**

Vamos tornar o prompt mais explícito, instruindo o modelo a retornar apenas a query SQL sem formatações adicionais.

### **Atualizar o `openai_service.py`**

**Localização:** `app/services/openai_service.py`

**Código Atualizado:**

```python
import openai
from flask import current_app
import re

def init_openai():
    """
    Inicializa a chave da API da OpenAI a partir das configurações da aplicação.
    """
    openai.api_key = current_app.config['OPENAI_API_KEY']

def traduzir_para_query(schema, pergunta):
    """
    Converte uma pergunta em linguagem natural para uma query SQL utilizando a API da OpenAI.

    Args:
        schema (str): O schema do banco de dados em texto.
        pergunta (str): A pergunta em linguagem natural.

    Returns:
        str: A query SQL gerada ou uma mensagem de erro.
    """
    prompt = f"""
    Você é um assistente que converte perguntas em linguagem natural para queries SQL do MySQL, usando o seguinte schema do banco de dados:

    {schema}

    Pergunta: {pergunta}

    Retorne apenas a query SQL sem qualquer formatação adicional ou blocos de código.
    """

    try:
        # Utilizando a interface atualizada da API ChatCompletion
        response = openai.ChatCompletion.create(
            model="gpt-4",  # ou outro modelo disponível
            messages=[
                {"role": "system", "content": "Você converte perguntas em linguagem natural para queries SQL do MySQL."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,  # Para respostas mais determinísticas
        )

        # Extrair apenas o conteúdo da mensagem
        query = response['choices'][0]['message']['content'].strip()

        # Remover possíveis blocos de código Markdown
        # Remove ```sql e ```
        query = re.sub(r'^```sql\s*', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\s*```$', '', query, flags=re.IGNORECASE)

        # Opcional: Remover quaisquer outras marcas de bloco de código
        query = re.sub(r'^```.*\n', '', query, flags=re.MULTILINE)
        query = re.sub(r'\n```$', '', query, flags=re.MULTILINE)

        # Validação simples: Garantir que a query começa com SELECT
        if not re.match(r'^SELECT', query, re.IGNORECASE):
            raise ValueError("A query gerada não é uma SELECT. Somente queries SELECT são permitidas.")

        return query
    except Exception as e:
        current_app.logger.error(f"Erro na tradução para query: {e}")
        return f"Erro na tradução da pergunta: {str(e)}"
```

### **Explicação das Alterações:**

1. **Ajuste no Prompt:**
   - Adicionamos a instrução explícita: "Retorne apenas a query SQL sem qualquer formatação adicional ou blocos de código."
   - Isso orienta o modelo a evitar a inclusão de blocos de código Markdown.

2. **Remoção de Blocos de Código no Código:**
   - Utilizamos expressões regulares (`re.sub`) para remover qualquer formatação de bloco de código que o modelo possa ter incluído.
   - As linhas de regex removem prefixos e sufixos de blocos de código, como ```sql e ```.

3. **Validação da Query:**
   - Mantivemos a validação para garantir que a query começa com `SELECT`, aumentando a segurança.

## **Passo 2: Atualizar o Template HTML (Opcional mas Recomendado)**

Embora o erro principal esteja relacionado à query SQL, é uma boa prática ajustar a interface para exibir mensagens de erro de forma mais amigável.

### **Atualizar `index.html`**

**Localização:** `app/templates/index.html`

**Código Atualizado:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat SQL Bot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
        }
        textarea {
            width: 100%;
            padding: 10px;
            font-size: 16px;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            margin-top: 10px;
        }
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            overflow-x: auto;
        }
        .error {
            color: red;
        }
    </style>
</head>
<body>
    <h1>Chat SQL Bot</h1>
    <textarea id="pergunta" rows="4" cols="50" placeholder="Digite sua pergunta..."></textarea><br>
    <button onclick="enviarPergunta()">Enviar</button>
    <h2>Query Gerada:</h2>
    <pre id="query"></pre>
    <h2>Resultados:</h2>
    <pre id="resultados"></pre>

    <script>
        async function enviarPergunta() {
            const pergunta = document.getElementById('pergunta').value;
            const response = await fetch('/pergunta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ pergunta }),
            });
            const data = await response.json();
            if(data.erro){
                document.getElementById('query').innerText = "";
                document.getElementById('resultados').innerHTML = `<span class="error">${data.erro}</span>`;
            } else {
                document.getElementById('query').innerText = data.query;
                document.getElementById('resultados').innerText = JSON.stringify(data.resultados, null, 2);
            }
        }
    </script>
</body>
</html>
```

### **Explicação das Alterações:**

- **Classe CSS `.error`:** Adicionamos uma classe para estilizar mensagens de erro em vermelho.
- **Exibição de Erros:** Modificamos a exibição de erros para usar `<span class="error">`, garantindo que mensagens de erro sejam facilmente visíveis.

## **Passo 3: Ajustar o Serviço de Banco de Dados para Segurança Adicional**

Embora já tenhamos restrito as queries a apenas `SELECT`, podemos adicionar mais verificações para garantir que as queries não contenham comandos indesejados.

### **Atualizar `db_service.py`**

**Localização:** `app/services/db_service.py`

**Código Atualizado:**

```python
import mysql.connector
from mysql.connector import Error
from flask import current_app
import re

def executar_query(query, params=None):
    # Apenas permitir queries SELECT para segurança
    if not re.match(r'^SELECT\b', query, re.IGNORECASE):
        return "Somente queries SELECT são permitidas para segurança."

    # Verificar se a query contém comandos indesejados
    # Como DELETE, UPDATE, DROP, etc.
    unsafe_patterns = [
        r'\bDELETE\b',
        r'\bUPDATE\b',
        r'\bDROP\b',
        r'\bINSERT\b',
        r'\bALTER\b',
        r'\bTRUNCATE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
    ]

    for pattern in unsafe_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return f"Comando SQL não permitido detectado na query: '{pattern.strip(r'\b')}'"

    try:
        connection = mysql.connector.connect(
            host=current_app.config['DB_HOST'],
            database=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD']
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            return resultados
    except Error as e:
        current_app.logger.error(f"Erro ao executar a query: {e}")
        return f"Erro ao executar a query: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
```

### **Explicação das Alterações:**

- **Verificação de Comandos Indesejados:** Adicionamos uma lista de padrões (`unsafe_patterns`) que representam comandos SQL potencialmente perigosos. A função agora verifica se a query contém algum desses comandos e retorna uma mensagem de erro caso detecte.
- **Melhoria na Segurança:** Essas verificações adicionais ajudam a prevenir que queries maliciosas sejam executadas, aumentando a segurança da aplicação.

## **Passo 4: Testar a Aplicação**

Após realizar as alterações, vamos testar a aplicação para garantir que tudo está funcionando corretamente.

### **1. Ativar o Ambiente Virtual (se ainda não estiver ativo):**

```bash
# No Linux/Mac
source venv/bin/activate

# No Windows
venv\Scripts\activate
```

### **2. Executar a Aplicação Flask:**

```bash
python run.py
```

### **3. Acessar a Aplicação no Navegador:**

Abra o navegador e vá para: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

### **4. Testar o Chatbot:**

**Exemplo de Pergunta:**

> Quais são os nomes e e-mails dos clientes que fizeram pedidos acima de 100 unidades em 2023?

**Esperada Query SQL Gerada:**

```sql
SELECT c.nome, c.email
FROM clientes c
JOIN pedidos p ON c.id = p.cliente_id
WHERE p.total > 100 AND YEAR(p.data) = 2023;
```

**Resultados Esperados:**

Uma tabela exibindo os nomes e e-mails dos clientes que cumpram os critérios especificados.

### **5. Verificar se o Erro foi Resolvido:**

- A query SQL gerada deve **não** conter blocos de código Markdown (`````sql e `````).
- A query deve ser executada corretamente no MySQL sem erros de sintaxe.
- Se ainda surgir algum erro, verifique os logs para detalhes em `logs/meu_chatbot.log`.

## **Passo 5: Adicionar Tratamento Adicional no Código (Opcional)**

Para garantir ainda mais robustez, podemos adicionar um tratamento adicional para remover qualquer formatação inadvertida.

### **Atualizar `openai_service.py` com Função de Limpeza:**

**Código Atualizado:**

```python
import openai
from flask import current_app
import re

def init_openai():
    """
    Inicializa a chave da API da OpenAI a partir das configurações da aplicação.
    """
    openai.api_key = current_app.config['OPENAI_API_KEY']

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

    Args:
        schema (str): O schema do banco de dados em texto.
        pergunta (str): A pergunta em linguagem natural.

    Returns:
        str: A query SQL gerada ou uma mensagem de erro.
    """
    prompt = f"""
    Você é um assistente que converte perguntas em linguagem natural para queries SQL do MySQL, usando o seguinte schema do banco de dados:

    {schema}

    Pergunta: {pergunta}

    Retorne apenas a query SQL sem qualquer formatação adicional ou blocos de código.
    """

    try:
        # Utilizando a interface atualizada da API ChatCompletion
        response = openai.ChatCompletion.create(
            model="gpt-4",  # ou outro modelo disponível
            messages=[
                {"role": "system", "content": "Você converte perguntas em linguagem natural para queries SQL do MySQL."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,  # Para respostas mais determinísticas
        )

        # Extrair apenas o conteúdo da mensagem
        query = response['choices'][0]['message']['content'].strip()

        # Limpar a query de quaisquer blocos de código Markdown
        query = limpar_query(query)

        # Validação simples: Garantir que a query começa com SELECT
        if not re.match(r'^SELECT\b', query, re.IGNORECASE):
            raise ValueError("A query gerada não é uma SELECT. Somente queries SELECT são permitidas.")

        return query
    except Exception as e:
        current_app.logger.error(f"Erro na tradução para query: {e}")
        return f"Erro na tradução da pergunta: {str(e)}"
```

### **Explicação das Alterações:**

1. **Função `limpar_query`:**
   - Cria uma função dedicada para remover qualquer formatação de bloco de código Markdown da query.
   - Remove qualquer ocorrência de ```sql no início e ``` no fim, além de qualquer outra marcação de bloco de código.

2. **Uso da Função `limpar_query`:**
   - Após extrair a query da resposta do modelo, passamos pela função `limpar_query` para garantir que não haja formatações indesejadas.

## **Considerações Finais**

### **Resumo das Soluções Adotadas:**

1. **Ajuste no Prompt:**
   - Orientamos o modelo a retornar apenas a query SQL sem formatações auxiliares.

2. **Limpeza da Resposta:**
   - Implementamos funções para remover blocos de código Markdown da resposta do modelo, assegurando que apenas a query SQL seja extraída e executada.

3. **Validações de Segurança:**
   - Mantivemos e aprimoramos as validações para garantir que apenas queries `SELECT` sejam executadas e que comandos perigosos sejam bloqueados.

4. **Melhorias na Interface:**
   - Ajustamos o frontend para exibir mensagens de erro de forma clara e amigável.

### **Próximos Passos Recomendados:**

1. **Testes Abrangentes:**
   - Realize vários testes com diferentes perguntas para garantir que as queries geradas estejam corretas e sem formatações indesejadas.

2. **Logging e Monitoramento:**
   - Monitore os logs regularmente para identificar e resolver quaisquer problemas que possam surgir.

3. **Implementar Autenticação:**
   - Considere adicionar mecanismos de autenticação à sua aplicação para controlar o acesso e aumentar a segurança.

4. **Melhorar Validações:**
   - Adicione validações mais robustas para garantir que as queries geradas estejam corretas e otimizadas.

5. **Documentação e Comentários:**
   - Continue adicionando comentários e documentação ao código para facilitar a manutenção futura.

Se após essas alterações você ainda enfrentar problemas ou precisar de assistência adicional, por favor, me avise para que possamos resolver juntos!