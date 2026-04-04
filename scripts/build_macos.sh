#!/bin/bash
# Build macOS zip for Novel Reader

set -e

APP_NAME="novel-reader"
VERSION="${VERSION:-dev}"

echo "Building macOS zip for $APP_NAME $VERSION"

# Build with PyInstaller if not already built
if [ ! -d "dist/$APP_NAME" ]; then
    echo "Building with PyInstaller..."
    pyinstaller novel_reader.spec --clean --noconfirm
fi

# Create macOS app bundle structure
APP_BUNDLE="$APP_NAME.app"
rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Create Info.plist
cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.novelreader.app</string>
    <key>CFBundleName</key>
    <string>Novel Reader</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
EOF

# Copy PyInstaller output to app bundle
cp -r dist/$APP_NAME/* "$APP_BUNDLE/Contents/MacOS/"

# Copy icon if available
if [ -f "icon.png" ]; then
    # Convert to icns if possible (requires iconutil)
    cp icon.png "$APP_BUNDLE/Contents/Resources/app_icon.png"
fi

# Create launcher script
cat > "$APP_BUNDLE/Contents/MacOS/novel-reader-launcher" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/novel-reader" "$@"
EOF
chmod +x "$APP_BUNDLE/Contents/MacOS/novel-reader-launcher"

# Create README
cat > "dist/README.txt" << 'EOF'
Novel Reader - 本地有声书管理器
================================

运行方式:
    双击 Novel Reader.app 启动程序

系统要求:
    - macOS 10.15 (Catalina) 或更高版本
    - Intel 或 Apple Silicon (M1/M2) 处理器

数据目录:
    - 配置: ~/Library/Application Support/novel-reader/config.json
    - 数据库: ~/Library/Application Support/novel-reader/library.db
    - 音频缓存: ~/Library/Application Support/novel-reader/audio/
    - TTS 模型: ~/Library/Application Support/novel-reader/models/

首次运行:
    如遇到"无法打开，因为无法验证开发者"的提示：
    1. 右键点击应用，选择"打开"
    2. 在弹出对话框中点击"打开"
    3. 或在系统偏好设置 -> 安全性与隐私中允许

项目主页:
    https://github.com/yourusername/novel-reader

问题反馈:
    请在 GitHub Issues 中报告问题
EOF

# Create zip archive
cd dist
zip -r "$APP_NAME-${VERSION}-macos.zip" "$APP_BUNDLE" README.txt
cd ..

echo "macOS zip created: dist/$APP_NAME-${VERSION}-macos.zip"
