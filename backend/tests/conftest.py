import os

# 测试使用独立密钥与内存数据库，绝不修改本机 MySQL 中的业务数据。
os.environ["JWT_SECRET_KEY"] = "test-only-signing-key-at-least-32-characters"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.security import hash_password


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory.begin() as db:
        db.add(User(username="admin", password_hash=hash_password("Admin@123456")))

    def override_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def headers(client):
    response = client.post(
        "/api/auth/login", data={"username": "admin", "password": "Admin@123456"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def product():
    return {
        "name": "测试耳机",
        "sku": "test-001",
        "category": "数码配件",
        "price": "99.90",
        "stock": 5,
        "status": "active",
        "description": "测试数据",
    }
