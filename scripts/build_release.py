"""构建前端并打包宝塔发布文件；生产密钥和数据库配置单独上传。"""

import shutil
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    npm = shutil.which("npm")
    if npm is None:
        raise SystemExit("未找到 npm，请先安装 Node.js 22.12+ 和前端依赖。")
    subprocess.run([npm, "run", "build:prod"], cwd=ROOT / "frontend", check=True)

    files = [
        ROOT / "README.md",
        ROOT / "backend/requirements.txt",
        ROOT / "backend/.env.example",
        ROOT / "backend/.env.production.example",
        ROOT / "backend/scripts/setup_env.py",
        ROOT / "backend/scripts/start_prod.sh",
        ROOT / "deploy/README.md",
        ROOT / "deploy/nginx.conf",
        ROOT / "deploy/supervisor.conf",
    ]
    files.extend((ROOT / "backend/app").rglob("*.py"))
    files.extend(path for path in (ROOT / "frontend/dist").rglob("*") if path.is_file())

    release_dir = ROOT / "release"
    release_dir.mkdir(exist_ok=True)
    archive = release_dir / "goodstock-production.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as package:
        for path in sorted(files):
            package.write(path, arcname=path.relative_to(ROOT))

    print(f"发布包：{archive}")
    print("解压目录：/www/wwwroot/124.223.60.74")
    print("请另行上传 backend/.env.production，发布包不包含数据库密码和密钥。")


if __name__ == "__main__":
    main()
