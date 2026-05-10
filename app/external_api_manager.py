# app/external_api_manager.py

class ExternalAPIManager:
    """Classe para gerenciar interações com APIs externas."""

    def __init__(self, logger):
        self.logger = logger

    def fetch_data(self, api_endpoint: str, params: dict) -> dict:
        """Busca dados de um endpoint API externo."""
        import requests
        
        self.logger.info(f"Consultando API: {api_endpoint} com params: {params}")
        response = requests.get(api_endpoint, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Erro ao consultar API: {response.status_code}")
            return {}

    def post_data(self, api_endpoint: str, data: dict) -> dict:
        """Envia dados para um endpoint API externo."""
        import requests
        
        self.logger.info(f"Enviando dados para API: {api_endpoint} com dados: {data}")
        response = requests.post(api_endpoint, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Erro ao enviar dados para API: {response.status_code}")
            return {}