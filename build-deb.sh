#!/bin/sh
# Build build/number-cruncher_<version>_all.deb from this source tree.
set -eu
umask 022

cd "$(dirname "$0")"
VERSION=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' number_cruncher/__init__.py)
PKG=build/number-cruncher_${VERSION}_all
DEB=$PKG.deb

rm -rf "$PKG" "$DEB"
install -d "$PKG/DEBIAN" \
    "$PKG/usr/games" \
    "$PKG/usr/share/number-cruncher/number_cruncher" \
    "$PKG/usr/share/applications" \
    "$PKG/usr/share/icons/hicolor/scalable/apps" \
    "$PKG/usr/share/doc/number-cruncher"

install -m 644 number_cruncher/*.py "$PKG/usr/share/number-cruncher/number_cruncher/"
install -m 755 packaging/number-cruncher "$PKG/usr/games/"
install -m 644 packaging/number-cruncher.desktop "$PKG/usr/share/applications/"
install -m 644 packaging/number-cruncher.svg "$PKG/usr/share/icons/hicolor/scalable/apps/"
install -m 644 README.md "$PKG/usr/share/doc/number-cruncher/"

SIZE=$(du -sk --exclude=DEBIAN "$PKG" | cut -f1)
sed -e "s/@VERSION@/$VERSION/" -e "s/@SIZE@/$SIZE/" packaging/control.in > "$PKG/DEBIAN/control"

dpkg-deb --root-owner-group --build "$PKG" "$DEB" >/dev/null
echo "$DEB"
