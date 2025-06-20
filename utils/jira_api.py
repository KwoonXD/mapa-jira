import requests

class JiraAPI:
    def __init__(self, email, token, url):
        self.auth = (email, token)
        self.url = url.rstrip("/") + "/rest/api/3"

    def buscar_chamados(self, jql, fields="summary"):
        chamados = []
        start = 0
        while True:
            params = {
                "jql": jql,
                "fields": fields,
                "startAt": start,
                "maxResults": 100
            }
            resp = requests.get(f"{self.url}/search", auth=self.auth, params=params)
            resp.raise_for_status()
            data = resp.json()
            chamados += data.get("issues", [])
            if start + 100 >= data.get("total", 0):
                break
            start += 100
        return chamados
