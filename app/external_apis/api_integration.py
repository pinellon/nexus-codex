import requests

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        response = requests.get(f"{self.base_url}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: dict | None = None) -> dict:
        response = requests.post(f"{self.base_url}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()


def example_api_usage():
    api_client = APIClient("https://api.publicapis.org")
    response = api_client.get("entries")
    print("API Entries:", response)

if __name__ == "__main__":
    example_api_usage()