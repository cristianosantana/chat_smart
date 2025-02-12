
import unittest
from unittest.mock import patch
from app import create_app
from app.services.db_service import executar_query

class TestDBService(unittest.TestCase):
    def setUp(self):
        # Criar uma instância da aplicação para usar no contexto
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Remover o contexto após o teste
        self.app_context.pop()

    @patch('app.services.db_service.mysql.connector.connect')
    def test_executar_query_select(self, mock_connect):
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [{'id': 1, 'nome': 'João'}]
        mock_conn.is_connected.return_value = True

        query = "SELECT * FROM clientes;"
        resultados = executar_query(query)
        self.assertEqual(resultados, [{'id': 1, 'nome': 'João'}])

    @patch('app.services.db_service.mysql.connector.connect')
    def test_executar_query_non_select(self, mock_connect):
        query = "DELETE FROM clientes WHERE id=1;"
        resultados = executar_query(query)
        self.assertEqual(resultados, "Somente queries SELECT são permitidas para segurança.")

if __name__ == '__main__':
    unittest.main()