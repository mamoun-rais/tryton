#!/bin/sh
set -e
version=`python setup.py --version`
python setup-freeze.py bdist_mac
rm -rf dist
mkdir dist
mv build/Tryton.app dist/
for f in CHANGELOG COPYRIGHT LICENSE README; do
    cp ${f} dist/${f}.txt
done
cp -r doc dist/
rm -f "tryton-${version}.dmg"
hdiutil create "tryton-${version}.dmg" -volname "Tryton Client ${version}" \
    -fs HFS+ -srcfolder dist
