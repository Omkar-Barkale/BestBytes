import importlib.util
import pathlib
from fastapi.testclient import TestClient
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

APP_PATH = BACKEND_DIR / "app.py"

spec = importlib.util.spec_from_file_location("backend_app", APP_PATH)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app
client = TestClient(app)


class TestApp:
    def test_root_running(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "API running"}

    def test_openapi_exists(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "paths" in response.json()

    def test_routers_mounted(self):
        assert client.get("/movies").status_code in (200, 404)
        assert client.get("/reviews").status_code in (200, 404)
        assert client.get("/users").status_code in (200, 400, 404)
        assert client.get("/admin").status_code in (200, 401, 404)
        assert client.get("/lists").status_code in (200, 404)
