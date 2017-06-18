#!/bin/sh

PREFIX="/usr/local"

echo "Remove app from $PREFIX/bin/amv"
rm -v "$PREFIX/bin/fir"

echo "Remove project files from $PREFIX/share/autorerename"
rm -Rv "$PREFIX/share/autorerename"

echo "Done"
