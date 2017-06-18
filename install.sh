#!/bin/sh

PREFIX="/usr/local"

echo "Copying project files to $PREFIX/share/autorerename"
mkdir -p "$PREFIX/share/autorerename"
cp -vR LICENSE README.md src/ "$PREFIX/share/autorerename"

echo "Install app at $PREFIX/bin/fir"
ln -vsT "$PREFIX/share/autorerename/src/main.py" "$PREFIX/bin/fir"
chmod +x "$PREFIX/bin/fir"

echo "Done"
