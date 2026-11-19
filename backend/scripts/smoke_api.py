"""先启动后端，再运行此脚本，验证真实 HTTP + MySQL 增删改查。"""

import argparse
from uuid import uuid4

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=15) as client:
        assert client.get("/api/products").status_code == 401
        response = client.post(
            "/api/auth/login", data={"username": "admin", "password": "Admin@123456"}
        )
        response.raise_for_status()
        client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
        assert client.get("/api/auth/me").json()["username"] == "admin"
        product = {
            "name": "自动验证商品",
            "sku": f"SMOKE-{uuid4().hex[:10].upper()}",
            "category": "数码配件",
            "price": "12.34",
            "stock": 7,
            "status": "active",
            "description": "验证后自动删除",
        }
        created = client.post("/api/products", json=product)
        assert created.status_code == 201, created.text
        product_id = created.json()["id"]
        try:
            assert client.get(f"/api/products/{product_id}").json()["price"] == "12.34"
            assert client.post("/api/products", json=product).status_code == 409
            product.update(price="56.78", stock=13, name="已更新的自动验证商品")
            updated = client.put(f"/api/products/{product_id}", json=product)
            assert updated.status_code == 200, updated.text
            assert updated.json()["price"] == "56.78"
            assert updated.json()["stock"] == 13
            page = client.get("/api/products", params={"q": product["sku"]}).json()
            assert page["total"] == 1
            assert page["items"][0]["name"] == product["name"]
            assert client.get("/api/products/stats").status_code == 200
        finally:
            assert client.delete(f"/api/products/{product_id}").status_code == 204
        assert client.get(f"/api/products/{product_id}").status_code == 404
    print("真实 API 验证通过：未登录拦截、登录、当前用户、创建、查询、重复校验、修改、删除。")


if __name__ == "__main__":
    main()
