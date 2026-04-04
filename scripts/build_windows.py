"""
Build Windows executable for Novel Reader
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_windows():
    """Build Windows executable"""
    print("Building Windows executable...")

    # Build with PyInstaller if not already built
    dist_dir = Path("dist")
    build_dir = Path("dist/novel-reader")

    if not build_dir.exists():
        print("Running PyInstaller...")
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "novel_reader.spec",
            "--clean",
            "--noconfirm"
        ], check=True)

    # Create standalone installer directory
    installer_dir = dist_dir / "novel-reader-windows"
    if installer_dir.exists():
        shutil.rmtree(installer_dir)
    installer_dir.mkdir()

    # Copy all files from PyInstaller output
    shutil.copytree(build_dir, installer_dir / "novel-reader", dirs_exist_ok=True)

    # Create README
    readme_content = """Novel Reader - 本地有声书管理器
================================

运行方式:
    双击 novel-reader.exe 启动程序

系统要求:
    - Windows 10/11 (x64)
    - 无需额外依赖

数据目录:
    - 配置: %APPDATA%\\novel-reader\\config.json
    - 数据库: %LOCALAPPDATA%\\novel-reader\\library.db
    - 音频缓存: %LOCALAPPDATA%\\novel-reader\\audio\\
    - TTS 模型: %LOCALAPPDATA%\\novel-reader\\models\\

项目主页:
    https://github.com/yourusername/novel-reader

问题反馈:
    请在 GitHub Issues 中报告问题
"""

    (installer_dir / "README.txt").write_text(readme_content, encoding='utf-8')

    # Create batch file for easy start
    batch_content = """@echo off
cd /d "%~dp0"
start "" "novel-reader\\novel-reader.exe"
"""
    (installer_dir / "启动.bat").write_text(batch_content, encoding='gbk')

    print(f"Windows build created at: {installer_dir}")

    # Create ZIP archive
    import zipfile
    version = os.environ.get("VERSION", "dev")
    zip_name = f"dist/novel-reader-{version}-windows.zip"

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in installer_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(installer_dir)
                zipf.write(file, arcname)

    print(f"ZIP archive created: {zip_name}")

if __name__ == "__main__":
    build_windows()
