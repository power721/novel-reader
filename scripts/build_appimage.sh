#!/bin/bash
# Build Linux AppImage for Novel Reader

set -e

APP_NAME="novel-reader"
APP_VERSION="${VERSION:-dev}"
ARCH="x86_64"

echo "Building AppImage for $APP_NAME $APP_VERSION"

# Install appimage-builder if not present
if ! command -v appimage-builder &> /dev/null; then
    pip install appimage-builder
fi

# Build with PyInstaller first if not already built
if [ ! -d "dist/$APP_NAME" ]; then
    echo "Building with PyInstaller..."
    pyinstaller novel_reader.spec --clean --noconfirm
fi

# Create AppImage directory structure
APPDIR="$APP_NAME.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/lib"

# Copy PyInstaller output
cp -r dist/$APP_NAME/* "$APPDIR/usr/bin/"

# Create AppRun
cat > "$APPDIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/novel-reader" "$@"
APPRUN_EOF
chmod +x "$APPDIR/AppRun"

# Create .desktop file
cat > "$APPDIR/$APP_NAME.desktop" << 'DESKTOP_EOF'
[Desktop Entry]
Name=Novel Reader
Comment=本地有声书管理器
Exec=novel-reader
Icon=novel-reader
Type=Application
Categories=AudioVideo;Audio;
Terminal=false
DESKTOP_EOF

# Copy icon if available
if [ -f "icon.png" ]; then
    cp icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"
    cp icon.png "$APPDIR/$APP_NAME.png"
fi

# Download AppImage runtime
wget -q -c "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage" -O /tmp/appimagetool || true
if [ ! -f "/tmp/appimagetool" ]; then
    echo "Warning: Could not download appimagetool, creating simple archive instead"
    cd dist
    tar -czf "$APP_NAME-${APP_VERSION}-${ARCH}.tar.gz" "$APP_NAME"
    echo "Created tar.gz: dist/$APP_NAME-${APP_VERSION}-${ARCH}.tar.gz"
    exit 0
fi

chmod +x /tmp/appimagetool

# Build AppImage
/tmp/appimagetool --no-appstream "$APPDIR" "dist/$APP_NAME-${APP_VERSION}-${ARCH}.AppImage"

echo "AppImage created: dist/$APP_NAME-${APP_VERSION}-${ARCH}.AppImage"
