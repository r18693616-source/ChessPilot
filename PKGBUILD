# Maintainer: OTAKUWeBer
pkgname=chesspilot
pkgver=1.0.0
pkgrel=1
pkgdesc="ChessPilot chess‑automation GUI (AppImage)"
arch=('x86_64')
url="https://github.com/OTAKUWeBer/ChessPilot"
license=('MIT')

# Runtime dependencies: FUSE for mounting AppImage, plus Stockfish engine
depends=('fuse2' 'stockfish')

# Upstream AppImage and local desktop/icon files
source=(
  "https://github.com/OTAKUWeBer/ChessPilot/releases/download/v${pkgver}/ChessPilot-${pkgver}.AppImage"
  "chesspilot.desktop"
  "chesspilot.png"
)

# Checksums: first for the AppImage, then desktop file, then icon
sha256sums=(
  '<APPIMAGE_SHA256>'   # e.g. 0123456789abcdef...
  'SKIP'                # you can SKIP the small desktop file if you prefer
  '<ICON_SHA256>'       # e.g. fedcba9876543210...
)

package() {
  # Install the AppImage as an executable wrapper
  install -Dm755 "${srcdir}/ChessPilot-${pkgver}.AppImage" \
                  "${pkgdir}/usr/bin/chesspilot"

  # Install the .desktop entry
  install -Dm644 "${srcdir}/chesspilot.desktop" \
                  "${pkgdir}/usr/share/applications/chesspilot.desktop"

  # Install the application icon
  install -Dm644 "${srcdir}/chesspilot.png" \
                  "${pkgdir}/usr/share/icons/hicolor/256x256/apps/chesspilot.png"
}
