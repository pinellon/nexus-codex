import urllib.request
import json

class WebResearcher:
    """Pesquisa soluções na internet"""
    
    def search_duckduckgo(self, query: str) -> str:
        """Busca no DuckDuckGo (sem API key)"""
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
                # Pega o abstract e os primeiros tópicos
                result = data.get("AbstractText", "")
                topics = [t.get("Text", "") for t in data.get("RelatedTopics", [])[:3]]
                return result + "\n" + "\n".join(topics)
        except Exception as e:
            return f"Erro na busca: {e}"
    
    def fetch_github_trending(self) -> str:
        """Pega projetos trending em Python pra se inspirar"""
        url = "https://api.github.com/search/repositories?q=language:python&sort=stars&order=desc&per_page=5"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Nexus/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                repos = data.get("items", [])
                return "\n".join([f"- {r['name']}: {r['description']}" for r in repos])
        except Exception as e:
            return f"Erro: {e}"
