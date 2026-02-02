"""基础测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthz():
    """测试健康检查"""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["code"] == 0
    assert response.json()["message"] == "ok"


def test_root():
    """测试根路由"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
