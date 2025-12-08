#!/bin/bash

set -e

TARGET="dist/nmkivy"

echo "Making release"
echo "Removing old dist"
rm -rf 'dist'
echo "Making new dist in $TARGET"
mkdir -p $TARGET

cp -r buttons $TARGET/
cp -r patches $TARGET/
cp main.kv $TARGET/
cp main.py $TARGET/
cp Style.py $TARGET/
cp utils.py $TARGET/
cp SPLogging.py $TARGET/
cp nmkivy.sh 'dist'/
cp -r locale $TARGET/
