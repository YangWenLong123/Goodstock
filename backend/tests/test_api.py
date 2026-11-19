from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import get_settings


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/products"),
        ("GET", "/api/products/stats"),
        ("GET", "/api/products/1"),
        ("POST", "/api/products"),
        ("PUT", "/api/products/1"),
        ("DELETE", "/api/products/1"),
        ("GET", "/api/auth/me"),
    ],
)
def test_all_business_routes_require_token(client, method, path):
    assert client.request(method, path).status_code == 401


def test_login_and_current_user(client, headers):
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert "password_hash" not in response.json()
    token = client.post(
        "/api/auth/login", data={"username": "admin", "password": "Admin@123456"}
    ).json()
    assert token["token_type"] == "bearer"
    assert token["expires_in"] == 3600


@pytest.mark.parametrize("username", ["admin", "unknown"])
def test_bad_credentials(client, username):
    response = client.post(
        "/api/auth/login", data={"username": username, "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


@pytest.mark.parametrize("kind", ["expired", "forged", "missing-exp", "unknown-user", "invalid"])
def test_invalid_tokens_are_rejected(client, kind):
    now = datetime.now(UTC)
    payload = {"sub": "1", "iat": now, "exp": now + timedelta(minutes=10)}
    secret = get_settings().jwt_secret_key
    if kind == "expired":
        payload["exp"] = now - timedelta(seconds=1)
    if kind == "missing-exp":
        del payload["exp"]
    if kind == "unknown-user":
        payload["sub"] = "999"
    if kind == "forged":
        secret = "a-different-signing-secret-at-least-32-characters"
    token = "not-a-token" if kind == "invalid" else jwt.encode(payload, secret, algorithm="HS256")
    response = client.get("/api/products", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_product_crud(client, headers, product):
    created = client.post("/api/products", headers=headers, json=product)
    assert created.status_code == 201
    data = created.json()
    product_id = data["id"]
    assert data["sku"] == "TEST-001"
    assert data["price"] == "99.90"

    read = client.get(f"/api/products/{product_id}", headers=headers)
    assert read.json()["name"] == product["name"]
    assert client.get("/api/products", headers=headers).json()["total"] == 1

    product.update(name="新名称", price="19.95", stock=18, status="inactive")
    updated = client.put(f"/api/products/{product_id}", headers=headers, json=product)
    assert updated.status_code == 200
    assert updated.json()["name"] == "新名称"
    assert updated.json()["price"] == "19.95"

    deleted = client.delete(f"/api/products/{product_id}", headers=headers)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/api/products/{product_id}", headers=headers).status_code == 404
    assert client.get("/api/products", headers=headers).json()["total"] == 0


def test_duplicate_sku_returns_conflict_and_session_recovers(client, headers, product):
    assert client.post("/api/products", headers=headers, json=product).status_code == 201
    assert client.post("/api/products", headers=headers, json=product).status_code == 409
    product["sku"] = "TEST-002"
    assert client.post("/api/products", headers=headers, json=product).status_code == 201


def test_filter_pagination_stats_and_literal_search(client, headers, product):
    for index in range(3):
        body = {**product, "sku": f"TEST-{index}", "name": f"测试耳机 {index}"}
        if index == 2:
            body.update(status="inactive", stock=20, category="生活用品")
        assert client.post("/api/products", headers=headers, json=body).status_code == 201

    page = client.get("/api/products?page=2&page_size=2", headers=headers).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1
    assert page["page"] == 2
    filtered = client.get(
        "/api/products", params={"category": "生活用品", "status": "inactive"}, headers=headers
    ).json()
    assert filtered["total"] == 1
    assert client.get("/api/products?q=TEST-1", headers=headers).json()["total"] == 1
    assert client.get("/api/products?q=%25", headers=headers).json()["total"] == 0
    assert client.get("/api/products?q=_", headers=headers).json()["total"] == 0
    assert client.get("/api/products?q=%27%20OR%201%3D1", headers=headers).json()["total"] == 0
    stats = client.get("/api/products/stats", headers=headers).json()
    assert stats == {"total": 3, "active": 2, "low_stock": 2, "inventory_value": "2997.00"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "   "),
        ("sku", "bad sku"),
        ("price", "0"),
        ("price", "-1"),
        ("price", "9.999"),
        ("stock", -1),
        ("stock", 1.5),
        ("stock", True),
        ("category", "不存在"),
        ("status", "bad"),
        ("name", None),
    ],
)
def test_invalid_product_is_rejected(client, headers, product, field, value):
    product[field] = value
    assert client.post("/api/products", headers=headers, json=product).status_code == 422


@pytest.mark.parametrize("query", ["page=0", "page_size=0", "page_size=101", "status=bad"])
def test_bad_pagination_or_filter(client, headers, query):
    assert client.get(f"/api/products?{query}", headers=headers).status_code == 422


def test_missing_product_and_empty_stats(client, headers, product):
    assert client.get("/api/products/999", headers=headers).status_code == 404
    assert client.put("/api/products/999", headers=headers, json=product).status_code == 404
    assert client.delete("/api/products/999", headers=headers).status_code == 404
    assert client.get("/api/products/stats", headers=headers).json() == {
        "total": 0,
        "active": 0,
        "low_stock": 0,
        "inventory_value": "0.00",
    }
