# Maintainer: OTAKUWeBer
pkgname=chesspilot
pkgver=1.0.0
pkgrel=1
pkgdesc="A fully offline chess autoplayer and position evaluator powered by ONNX and Stockfish"
arch=('x86_64')
url="https://github.com/OTAKUWeBer/ChessPilot"
license=('MIT')
depends=('stockfish' 'tk')
source=(
  "https://github.com/OTAKUWeBer/ChessPilot/releases/download/v${pkgver}/ChessPilot-${pkgver}-linux-x86_64"
  "chesspilot.desktop"
  "assets/chesspilot.png"
)
noextract=("ChessPilot-${pkgver}-linux-x86_64")
sha256sums=(
  '489b9a35147492f8dafa68d3694e7fc6dca15d7017b842ce040ae7b98362d065'  # Raw binary
  'SKIP'  # Desktop entry
  '8d304ed8f25461f6fc69d0144e0de68403f239b8583b5120fbb5f859254c74d9'  # Icon hash (replace if needed)
)

package() {
  install -Dm755 "$srcdir/ChessPilot-${pkgver}-linux-x86_64" \
    "$pkgdir/usr/bin/chesspilot"

  install -Dm644 "$srcdir/chesspilot.desktop" \
    "$pkgdir/usr/share/applications/chesspilot.desktop"

  install -Dm644 "$srcdir/assets/chesspilot.png" \
    "$pkgdir/usr/share/icons/hicolor/256x256/apps/chesspilot.png"

  install -Dm644 "$srcdir/LICENSE" \
    "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
