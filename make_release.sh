#!/bin/bash
set -e
echo "making a nmkivy for BTP "

NAME=dist

echo "Making release"
echo "Removing old dist"
rm -rf $NAME
echo "Making new dist"
mkdir $NAME

cd po
python3.8 Po2Mo.py
cd -

echo "Copy py files, excluding debug files"
cp *.py $NAME
cp main.kv $NAME
cp -r buttons locale patches $NAME
cp nmkivy.sh $NAME

# if we are on Ubuntu 18.04 we need to get the venv3.8 folder included
if [[ "$(cat /etc/issue)" == *"18.04"* ]]; then
    cp -r .venv3.8 $NAME
fi

rm $NAME/test*.py 2> /dev/null


echo "done"


