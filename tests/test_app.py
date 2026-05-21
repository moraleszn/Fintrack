# test_app.py
# Testes iniciais para o backend do Fintrack

def test_root():
    from fastapi.testclient import TestClient
    from backend.app import app
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bem-vindo ao Fintrack API!"}
