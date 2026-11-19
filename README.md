# Goodstock · Vue 3 + FastAPI 商品管理学习案例

一个可以连接本机 MySQL 的完整前后端案例。先登录获取 JWT Token，才能查看、新增、修改或删除商品。页面使用中文，适配电脑和手机。

生产访问地址为 `http://124.223.60.74`：参见 [宝塔部署文档](deploy/README.md)。在项目根目录运行 `python3 scripts/build_release.py` 可生成前后端发布包。

## 已实现功能

- 登录、退出、密码显示切换，密码通过 Argon2 哈希保存。
- JWT 签名校验、60 分钟有效期、过期自动回到登录页。
- 商品列表、单条详情、新增、编辑、删除确认。
- 按商品名称 / SKU 搜索，按分类 / 状态筛选，后端分页。
- SKU 唯一校验、金额精度校验、库存非负整数校验。
- 商品总数、在售商品、库存预警、库存总值统计。
- 加载、空列表、接口报错、重复提交等状态处理。
- Swagger 接口文档，后端自动化测试和真实数据库验证脚本。

## 技术选型

| 部分 | 技术 | 用途 |
| --- | --- | --- |
| 前端 | Vue 3、Vue Router、Vite | 页面、路由和开发代理 |
| 接口请求 | 浏览器原生 fetch | 统一附加 Token 和处理报错 |
| 后端 | Python 3.11+、FastAPI | REST API、依赖注入、参数校验 |
| ORM | SQLAlchemy 2 | Python 对象与数据库表之间的映射 |
| 数据库 | MySQL 8+、PyMySQL | 本地持久化存储 |
| 认证 | PyJWT、pwdlib / Argon2 | Token 签名与密码哈希 |

## 1. 安装后端并初始化 MySQL

先确认本机 MySQL 服务已启动。本例默认连接参数：

```text
地址：127.0.0.1
端口：3306
用户名：root
密码：root
数据库：fastapi_shop（初始化脚本自动创建）
```

在项目根目录打开终端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/setup_env.py
python -m app.init_db
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Windows 激活虚拟环境的命令为 `.venv\Scripts\activate`，其他 Python 命令相同。

`setup_env.py` 会从 `.env.example` 生成本地 `.env`，并自动生成随机 JWT 密钥。已有配置不会被覆盖。数据库用户名、密码、端口都可以在 `backend/.env` 中修改。**数据库密码只保存在后端，不会发送给前端。**

`app.init_db` 创建专用数据库、`users` 和 `products` 表，以及 12 条演示商品。重复执行不会重置现有账号；仅在商品表为空时插入演示商品。该脚本不会更改其他数据库。结构变更后，`create_all` 不会自动迁移已有表；进阶项目应使用 Alembic。

如果目录里已经有 `.venv`、`.env` 并且已初始化数据库，日常启动只需：

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## 2. 启动 Vue 3 前端

需要 Node.js 22.12+。另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

打开 **http://127.0.0.1:5174**。

| 项目 | 地址 / 账号 |
| --- | --- |
| 登录页面 | http://127.0.0.1:5174/login |
| 管理员用户名 | `admin` |
| 管理员密码 | `Admin@123456` |
| 后端地址 | http://127.0.0.1:8001 |
| 交互式 API 文档 | http://127.0.0.1:8001/docs |

开发环境通过 Vite 把 `/api` 请求代理到 `127.0.0.1:8001`。前后端端口分别为 **5174 / 8001**，避免与其他项目常用的 5173 / 8000 冲突。修改后端端口时，需要同时修改 `frontend/vite.config.js` 的代理地址。

## 3. 推荐的学习顺序

先让整个案例跑起来，再沿着一次请求阅读代码：

```text
登录表单 LoginView.vue
  → api.js 发送 username/password 表单
  → routers/auth.py 校验密码
  → security.py 签发 JWT
  → session.js 保存 Token
  → 商品页发出 Authorization: Bearer <token>
  → dependencies.py 校验签名、有效期、用户状态
  → routers/products.py 执行增删改查
  → models.py / SQLAlchemy 访问 MySQL
  → schemas.py 校验并序列化返回值
  → Vue 更新页面
```

### 项目结构

```text
fastApi-request/
├── README.md
├── backend/
│   ├── .env.example          # 数据库 / JWT 配置模板
│   ├── requirements.txt      # 运行依赖
│   ├── requirements-dev.txt  # 测试、代码检查依赖
│   ├── scripts/
│   │   ├── setup_env.py      # 生成配置和随机 JWT 密钥
│   │   └── smoke_api.py      # 验证真实 HTTP + MySQL 流程
│   ├── app/
│   │   ├── main.py           # FastAPI 入口、CORS、异常处理
│   │   ├── config.py         # 读取 .env
│   │   ├── database.py       # Engine、Session、依赖注入
│   │   ├── models.py         # users / products 数据库表
│   │   ├── schemas.py        # Pydantic 请求和响应模型
│   │   ├── security.py       # 密码哈希、JWT 签发
│   │   ├── dependencies.py   # Token 校验及当前登录用户
│   │   ├── init_db.py        # 创建数据库、表、初始数据
│   │   └── routers/
│   │       ├── auth.py       # 登录、当前用户
│   │       └── products.py   # 商品增删改查、统计
│   └── tests/                # 独立内存数据库测试
└── frontend/
    ├── vite.config.js        # Vue 插件、后端代理
    └── src/
        ├── main.js           # Vue 入口
        ├── App.vue           # Token 失效后的页面跳转
        ├── router.js         # 登录页、商品页、路由守卫
        ├── session.js        # sessionStorage 登录状态
        ├── api.js            # fetch 封装及业务接口
        ├── style.css         # 页面和响应式样式
        ├── components/       # 弹窗、商品表单、图标等
        └── views/
            ├── LoginView.vue
            └── ProductsView.vue
```

### 为什么要使用 Depends？

```python
# routers/products.py
router = APIRouter(
    prefix="/api/products",
    dependencies=[Depends(get_current_user)],
)
```

把认证依赖放在整个商品路由组上，所有商品接口都会先校验 Token。即使绕过前端直接请求接口，没有合法 Token 也会返回 `401`。

```python
# database.py
def get_db():
    with SessionLocal() as session:
        yield session
```

`Depends(get_db)` 为每个请求提供数据库会话。`yield` 后退出上下文，连接会归还连接池，无需在每个接口里重复写关闭连接的代码。

### 为什么金额返回字符串？

数据库使用 `DECIMAL(10, 2)`，Python 使用 `Decimal`，JSON 中价格序列化为 `"99.90"`，避免浮点数计算误差。前端仅在展示时转为 `Number` 格式化，提交时仍可以发送十进制字符串。

## 4. API 一览

除登录和健康检查外，下列接口均需要请求头 `Authorization: Bearer <access_token>`。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/api/auth/login` | 表单登录，返回 JWT 和用户信息 |
| GET | `/api/auth/me` | 获取当前用户 |
| GET | `/api/products` | 搜索、筛选、分页查询 |
| GET | `/api/products/stats` | 全部商品的统计 |
| GET | `/api/products/{id}` | 查看单个商品 |
| POST | `/api/products` | 新增商品，成功返回 201 |
| PUT | `/api/products/{id}` | 修改商品，提交完整可编辑字段 |
| DELETE | `/api/products/{id}` | 删除商品，成功返回 204 |
| GET | `/api/health` | 检查 API 进程是否运行，不检查数据库 |

列表查询参数：`q`、`category`、`status`、`page`、`page_size`。分类为 `数码配件 / 办公文具 / 生活用品 / 服饰箱包`；状态为 `active / inactive`；默认每页 8 条，最多 100 条。

错误状态：`401` 登录失效或凭据错误；`404` 商品不存在；`409` SKU 已存在；`422` 输入校验失败；`503` 数据库操作失败。

### 用 curl 观察登录和创建请求

```bash
# 登录使用表单，不是 JSON
curl -X POST http://127.0.0.1:8001/api/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=admin' \
  --data-urlencode 'password=Admin@123456'
```

响应示例（Token 仅作格式示意）：

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { "id": 1, "username": "admin", "display_name": "演示管理员" }
}
```

复制实际返回的 Token，替换下面的 `YOUR_TOKEN`：

```bash
curl http://127.0.0.1:8001/api/products \
  -H 'Authorization: Bearer YOUR_TOKEN'

curl -X POST http://127.0.0.1:8001/api/products \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"name":"学习用商品","sku":"LEARN-001","category":"数码配件","price":"99.90","stock":20,"status":"active","description":"我的第一个 FastAPI 商品"}'
```

也可以进入 `/docs`，点击 **Authorize**，使用 `admin / Admin@123456` 登录后直接调试商品接口。

## 5. 测试与构建

```bash
# 后端：已激活 backend/.venv，在 backend 目录执行
python -m pip install -r requirements-dev.txt
pytest -q
ruff check .
ruff format --check .

# 需先启动真实 MySQL 与后端；脚本会创建、验证并删除自己的测试商品
python scripts/smoke_api.py

# 前端：在 frontend 目录执行
npm run lint
npm run build
```

`pytest` 使用独立的 SQLite 内存数据库，验证权限、过期 / 伪造 Token、完整 CRUD、唯一约束、搜索筛选、分页、金额和库存校验等，不会修改 MySQL。`smoke_api.py` 补充验证真实 MySQL 的请求流程，默认使用演示管理员；修改演示密码后需同步调整脚本。

`npm run build` 输出 `frontend/dist`。`npm run preview` 只预览静态构建文件，不提供开发时的 API 代理；需要把 `/api` 反向代理到后端，或者在构建前设置 `VITE_API_BASE_URL`，并配置后端 CORS。使用 history 路由部署时，还需将未知前端路径回退到 `index.html`。

## 6. 常见问题与案例边界

- **数据库无法连接**：检查 MySQL 服务、3306 端口和 `.env` 配置。`localhost` 与 `127.0.0.1` 的数据库权限可能不同，本例明确使用 TCP 的 `127.0.0.1`。
- **提示 JWT 密钥缺失**：先在 `backend` 目录运行 `python scripts/setup_env.py`；不要把模板中的占位密钥当作真实密钥。
- **修改默认密码不生效**：`SEED_ADMIN_PASSWORD` 只用于首次创建账号，不会覆盖数据库里的已有密码。
- **前端接口连接失败**：确认后端监听 8001，检查 Vite 代理；代理配置修改后需要重启前端。
- **重复 SKU**：编码不区分手动输入的大小写，会统一转为大写；数据库唯一约束防止重复。
- **退出登录**：清除浏览器中的 Token；本例不实现服务端 Token 吊销，已签发 Token 会在 60 分钟后自然失效。
- **Token 存储**：本例使用 `sessionStorage`，刷新可保留，关闭标签页清除。它可被页面 JavaScript 访问，实际部署时应结合 XSS 防护评估 HttpOnly Cookie 方案。
- **定位**：这是单管理员学习案例，不含注册、角色权限、刷新 Token 和登录限流；对公网部署前应更换演示账号、使用数据库专用账号、HTTPS 并完善这些能力。
- **本地数据与时间**：数据库密码和随机密钥在被 Git 忽略的 `.env` 中；商品时间在数据库中使用 UTC 保存，页面转换为浏览器本地时间显示。
