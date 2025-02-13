from flask import Blueprint, render_template, request, jsonify
from .services.openai_service import traduzir_para_query
from .services.db_service import executar_query
from .utils import dados_para_tabela_html 

bp = Blueprint('main', __name__)

# Definição do schema do banco de dados
SCHEMA = """
"os": {
    "descricao": "Tabela de os (ordens de serviço) do sistema.",
    "colunas": ("id","os_concessionaria","tipo_atendimento","retencao_iss","paga","data_pagamento","fechada","data_fechamento","finalizada","data_finalizacao","cancelada","data_cancelamento","solicitado_cancelamento","os_retorno","cortesia_migrada","nivel_indicador1","nivel_indicador2","indicador1_id","indicador2_id","departamento_id","vendedor_id","concessionaria_id","cliente_carro_id","cliente_id","os_tipo_id","proposta_id","os_retorno_id","os_migracao_cortesia_id","ativo","created_at","deleted_at","id_antigo"),
    "relacionamentos": {
        "cliente_carros": "cliente_carros.id = os.cliente_carro_id",
        "clientes": "clientes.id = os.cliente_id",
        "concessionarias": "concessionarias.id = os.concessionaria_id",
        "departamentos": "departamentos.id = os.departamento_id",
        "funcionarios": "funcionarios.id = os.vendedor_id",
        "indicadores": "indicadores.id = os.indicador2_id",
        "os": "os.id = os.os_retorno_id",
        "os_tipos": "os_tipos.id = os.os_tipo_id",
        "pre_propostas": "pre_propostas.id = os.pre_proposta_id",
        "propostas": "propostas.id = os.proposta_id"
    }
},
"os_servicos": {
    "descricao": "Tabela de os_servicos (serviços de ordens de serviço) do sistema. tabela pivot entre 'os' e 'servicos'.",
    "colunas": ("id","codigo","valor_venda","valor_original","desconto_supervisao","desconto_migracao_cortesia","desconto_avista","valor_venda_real","os_tipo_id","desconto_bonus","fechado","codigo_fechamento","data_fechamento","fechado_sem_codigo","justificativa_sem_codigo","cancelado","data_cancelamento","solicitado_cancelamento","os_id","servico_id","tonalidade_id","combo_id","produtivo_id","concessionaria_execucao_id","ativo","created_at","deleted_at","plotter_corte_id"),
    "relacionamentos": {
        "combos": "combos.id = os_servicos.combo_id",
        "os": "os.id = os_servicos.os_id",
        "os_tipos": "os_tipos.id = os_servicos.os_tipo_id",
        "plotter_cortes": "plotter_cortes.id = os_servicos.plotter_corte_id",
        "funcionarios": "funcionarios.id = os_servicos.produtivo_id",
        "servicos": "servicos.id = os_servicos.servico_id",
        "tonalidades": "tonalidades.id = os_servicos.tonalidade_id",
        "concessionarias": "concessionarias.id = os_servicos.concessionaria_execucao_id"
    }
},
 "servicos": {
    "descricao": "Tabela de servicos (serviços) do sistema.",
    "colunas": ("id","nome","custo_fixo","codigo_nf","fecha_kit","fecha_peca_avulsa","fecha_peca","fecha_produto","fecha_produtivo","diferencia_departamento_preco","diferencia_porte","diferencia_departamento","diferencia_porte_comissao","diferencia_tempo_departamento","diferencia_tempo_cor","credito_necessario","valor_desconto_cortesia","aceita_desconto_cortesia","segunda_aplicacao","grupo_servico_id","subgrupo_servico_id","servico_categoria_id","tags","ativo","created_at","deleted_at"),
    "relacionamentos": {
        "grupos_servicos": "grupos_servicos.id = servicos.grupo_servico_id",
        "servico_categorias": "servico_categorias.id = servicos.servico_categoria_id",
        "subgrupos_servicos": "subgrupos_servicos.id = servicos.subgrupo_servico_id"
    }
},
"caixa_status": {
    "descricao": "Tabela de caixa_status",
    "colunas": ("id","nome","ativo"),
    "relacionamentos": {}
},
"caixa_tipos": {
    "descricao": "Tabela de caixa_tipos",
    "colunas": ("id","nome","ativo"),
    "relacionamentos": {}
},
"caixas": {
    "descricao": "Tabela de caixas (movimentações financeiras, se tiver um ou mais registros na tabela caixas a OS referente a este caixa foi paga!) do sistema.",
    "colunas": ("id","valor","data_vencimento","data_pagamento","cancelado","data_cancelamento","fechado","data_fechamento","classificado","data_classificacao","finalizado","verificado","data_verificacao","data_finalizacao","parcela","quant_parcelas","nome_depositante","codigo_transacao","nome_titular","doc_titular","telefone_titular","tid_cielo","bandeira_cartao","codigo_autorizacao","numero_autorizacao","nome_cartao","cc_conciliado","pix_payload","pix_info_pagador","pix_e2ed_id","pix_rtr_id","observacao_financeiro","caixa_preto","usuario_pagamento_id","usuario_verificacao_id","caixa_conta_id","caixa_tipo_id","caixa_pendente_id","caixa_status_id","caixa_fechamento_id","caixa_original_id","empresa_faturamento_id","financeiro_malote_classificacao_id","financeiro_caixa_destino_id","os_id","ativo","created_at","deleted_at"),
    "relacionamentos": {
        "caixa_contas": "caixa_contas.id = caixas.caixa_conta_id",
        "caixa_fechamentos": "caixa_fechamentos.id = caixas.caixa_fechamento_id",
        "caixas": "caixas.id = caixas.caixa_original_id",
        "caixas_pendentes": "caixas_pendentes.id = caixas.caixa_pendente_id",
        "caixa_status": "caixa_status.id = caixas.caixa_status_id",
        "caixa_tipos": "caixa_tipos.id = caixas.caixa_tipo_id",
        "empresas": "empresas.id = caixas.empresa_faturamento_id",
        "financeiro_caixas_destino": "financeiro_caixas_destino.id = caixas.financeiro_caixa_destino_id",
        "financeiro_malotes_classificacao": "financeiro_malotes_classificacao.id = caixas.financeiro_malote_classificacao_id",
        "os": "os.id = caixas.os_id",
        "usuarios": "usuarios.id = caixas.usuario_verificacao_id"
    }
},
"caixas_pendentes": {
    "descricao": "Tabela de caixas_pendentes (movimentações financeiras pendentes, se tiver registro existe uma promessa de pagamento) do sistema.",
    "colunas": ("id","valor","codigo_transacao","expiracao","pix_tx_id","pix_payload","pix_tentativas","pix_br_code","pix_info_pagador","pix_e2ed_id","pix_rtr_id","data_criacao_cobranca","data_expiracao_cobranca","fechado","data_fechamento","finalizado","data_finalizacao","cancelado","data_cancelamento","caixa_tipo_id","caixa_status_id","caixa_fechamento_id","os_id","empresa_id","remessa_os_id","tipo_remessa_id","usuario_pagamento_id","created_at","deleted_at"),
    "relacionamentos": {
        "caixa_fechamentos": "caixa_fechamentos.id = caixas_pendentes.caixa_fechamento_id",
        "caixa_status": "caixa_status.id = caixas_pendentes.caixa_status_id",
        "caixa_tipos": "caixa_tipos.id = caixas_pendentes.caixa_tipo_id",
        "empresas": "empresas.id = caixas_pendentes.empresa_id",
        "os": "os.id = caixas_pendentes.os_id",
        "remessa_os": "remessa_os.id = caixas_pendentes.remessa_os_id",
        "usuarios": "usuarios.id = caixas_pendentes.usuario_pagamento_id",
        "tipo_remessas": "tipo_remessas.id = caixas_pendentes.tipo_remessa_id"
    }
},
"concessionarias": {
    "descricao": "Tabela de concessionarias (concessionárias de veículos, onde nós vendemos serviços como terceiro!) do sistema.",
    "colunas": ("id","nome","aceita_indicador1","aceita_indicador2","produtivo_base_id","concessionaria_execucao_id","cluster_id","business_unit_id","empresa_faturamento_id","ativo","created_at","deleted_at"),
    "relacionamentos": {
        "business_units": "business_units.id = concessionarias.business_unit_id",
        "concessionarias": "concessionarias.id = concessionarias.concessionaria_execucao_id",
        "clusters": "clusters.id = concessionarias.cluster_id",
        "carro_marcas": "carro_marcas.id = concessionarias.carro_marca_id",
        "comissao_periodos": "comissao_periodos.id = concessionarias.comissao_periodo_id",
        "empresas": "empresas.id = concessionarias.empresa_faturamento_id",
        "nota_tipos": "nota_tipos.id = concessionarias.nota_tipo_id",
        "produtivo_bases": "produtivo_bases.id = concessionarias.produtivo_base_id",
        "funcionarios": "funcionarios.id = concessionarias.supervisor_vendas_id"
    }
},
"departamentos": {
    "descricao": "Tabela de departamentos (departamentos de vendas) do sistema.",
    "colunas": ("id","nome","sigla","sigla_carbel","ativo","created_at","deleted_at"),
    "relacionamentos": {}
}
"""

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/pergunta', methods=['POST'])
def pergunta():
    data = request.get_json()
    pergunta = data.get('pergunta')
    
    if not pergunta:
        return jsonify({"erro": "Pergunta não fornecida."}), 400

    # Traduzir pergunta para query SQL
    query_sql = traduzir_para_query(SCHEMA, pergunta)
    
    # Executar a query no banco de dados
    resultados = executar_query(query_sql)
    
    # Converter os resultados para uma tabela HTML
    tabela_html = dados_para_tabela_html(resultados) if isinstance(resultados, list) else resultados
    
    return jsonify({
        "query": query_sql,
        "tabela_html": tabela_html
    })