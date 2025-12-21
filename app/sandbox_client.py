import requests

SANDBOX_URL = "http://localhost:8000"

def run_code_in_sandbox(code: str):
    r = requests.post(SANDBOX_URL, json={"code": code}, timeout=15)
    return r.text
