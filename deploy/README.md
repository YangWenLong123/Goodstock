# 宝塔生产部署

生产访问地址为 `http://124.223.60.74`，使用服务器 IP 直接访问。
前端静态文件由 Nginx 提供；`/api` 转发给 `127.0.0.1:8001` 的 FastAPI。
数据库使用本机 MySQL，用户名为 `along`，数据库名沿用 `fastapi_shop`。
服务器项目根目录为 `/www/wwwroot/124.223.60.74`。

## 1. 本机打包

需要 Node.js 22.12+、Python 3.11+。首次先在 `frontend` 执行 `npm install`，然后在项目根目录执行：

```bash
python3 scripts/build_release.py
```

产物是 `release/goodstock-production.zip`，包含前端 `dist`、后端 Python 源码、依赖清单及宝塔配置。
后端以源码发布，虚拟环境和运行依赖在 Linux 服务器上安装。

只构建前端可执行：

```bash
cd frontend
npm run build:prod
```

`frontend/.env.production` 的 `VITE_API_BASE_URL` 保持为空，在 IP 站点中实际请求 `http://124.223.60.74/api/...`。
发布包通过文件白名单打包，不包含 `.env`、`.env.production`、虚拟环境、依赖目录、测试或缓存。

## 2. 上传文件和生产配置

在宝塔安装 Nginx、MySQL 8.0+、Python 3.12、Supervisor 管理器。
将发布 ZIP 解压至 `/www/wwwroot/124.223.60.74`，解压后应直接看到 `frontend`、`backend` 和 `deploy`。

将本机 `backend/.env.production` **单独上传**到服务器的：

```text
/www/wwwroot/124.223.60.74/backend/.env.production
```

该文件已填写提供的数据库账号、密码及独立生成的 JWT 密钥和管理员初始密码，并被 Git 忽略。
它应由后端运行用户读取，网站根目录只指向 `frontend/dist`。

已部署的服务器保留原有数据库配置、JWT 密钥和账号初始密码，只将现有 `.env.production` 的这一行更新为：

```dotenv
CORS_ORIGINS=["http://124.223.60.74"]
```

## 3. 创建数据库并安装后端

在宝塔创建数据库 `fastapi_shop`，授权用户 `along` 通过 `127.0.0.1` 访问该数据库。
如果宝塔中的数据库名不同，同步修改 `.env.production` 中的 `DB_NAME`。

在服务器终端执行，`python3.12` 可替换成宝塔安装的 Python 3.12 完整路径：

```bash
cd /www/wwwroot/124.223.60.74/backend
python3.12 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

如果已按上一步上传 `.env.production`，可以直接初始化数据库。
从全新 Git 检出部署、尚无生产配置时，先运行：

```bash
./.venv/bin/python scripts/setup_env.py --production
```

随后填写 `.env.production` 中的 `DB_PASSWORD`；该命令在已有配置时不会覆盖它。
`SEED_ADMIN_PASSWORD` 是首次初始化管理员使用的密码，可在建库前修改。

首次使用空数据库，执行：

```bash
APP_ENV=production ./.venv/bin/python -m app.init_db
```

这会建立表、管理员和演示商品。若需保留本机商品和 `test01` 等账号，先将本机 `fastapi_shop` 导出 SQL，再导入服务器数据库。
`SEED_ADMIN_PASSWORD` 不会重设导入数据库中已有账号的密码。

设置供宝塔 `www` 用户读取的权限：

```bash
chown -R www:www /www/wwwroot/124.223.60.74/backend
chmod 600 /www/wwwroot/124.223.60.74/backend/.env.production
```

本地开发继续读取 `.env`；设置 `APP_ENV=production` 才会读取 `.env.production`。

## 4. 启动后端

先前台验证启动，检查无报错后按 Ctrl+C 结束，再交给 Supervisor：

```bash
cd /www/wwwroot/124.223.60.74/backend
bash scripts/start_prod.sh
```

脚本启用生产配置，以 2 个 Uvicorn worker 监听 `127.0.0.1:8001`，由 Nginx 转发请求。

在宝塔 Supervisor 管理器添加守护进程：

| 项目 | 值 |
| --- | --- |
| 名称 | `goodstock-api` |
| 工作目录 | `/www/wwwroot/124.223.60.74/backend` |
| 启动命令 | `/bin/bash /www/wwwroot/124.223.60.74/backend/scripts/start_prod.sh` |
| 运行用户 | `www` |
| 进程数量 | `1`（脚本内部启动 2 个 worker） |
| 自动启动、自动重启 | 启用 |

也可将 `deploy/supervisor.conf` 的内容合并到宝塔 Supervisor 实际加载的进程配置中，重新加载后启动。
日志路径配置为 `/www/wwwlogs/goodstock-api.log`。

## 5. 配置 IP 网站

1. 放行服务器安全组和宝塔防火墙的公网 80 端口，IP 访问无需配置 DNS。
2. 宝塔添加静态站点或修改现有站点，在「域名管理」绑定 `124.223.60.74`，根目录填 `/www/wwwroot/124.223.60.74/frontend/dist`。
3. 使用 `deploy/nginx.conf` 中的 HTTP 站点配置；确认该 IP 只绑定到当前站点，避免被其他站点接收。
4. 关闭该站点此前的「强制 HTTPS」，移除指向旧域名的重定向，检查配置后重载 Nginx。

当前访问入口为 `http://124.223.60.74`。如以后启用 HTTPS，需先配置适用于该 IP 的证书，再更新访问地址和 CORS。

`proxy_pass http://127.0.0.1:8001;` 末尾不追加 `/`，确保后端收到完整 `/api/...` 路径。
Vue history 路由通过 `try_files` 回退到 `index.html`，刷新 `/login` 也能打开页面。
后端 8001、MySQL 3306 只需本机访问。

## 6. 验证及更新

服务器终端检查：

```bash
curl http://127.0.0.1:8001/api/health
curl http://124.223.60.74/api/health
```

两者应返回 `{"status":"ok"}`。再访问 `http://124.223.60.74/login`，使用数据库中的账号登录并查询商品，确认数据库连接正常。
空数据库首次初始化的管理员用户名及密码以服务器 `.env.production` 中的 `SEED_ADMIN_USERNAME`、`SEED_ADMIN_PASSWORD` 为准。
接口文档为 `http://124.223.60.74/docs`。

更新时重新打包、上传解压，然后在 Supervisor 中重启 `goodstock-api`。
如运行依赖有变化，先重新安装 `requirements.txt`。
发布包不包含 `.env.production`，因此更新代码会保留服务器原有密钥和数据库配置。

常见定位：`502` 检查 Supervisor 和 8001；`503` 检查数据库和生产配置；页面刷新 `404` 检查 Nginx 的 `try_files`。
