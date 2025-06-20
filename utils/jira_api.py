import requests
from requests.auth import HTTPBasicAuth

class JiraAPI:
    def __init__(self, email, api_token, domain):
        self.auth = HTTPBasicAuth(email, api_token)
        self.domain = domain
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def buscar_chamados(self, jql, fields="summary"):
        url = f"{self.domain}/rest/api/3/search"
        params = {
            "jql": jql,
            "fields": fields,
            "maxResults": 1000
        }
        response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
        response.raise_for_status()
        return response.json()["issues"]
