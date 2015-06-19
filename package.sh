set -e -x
cp env "$HOME/$prefix"
tar -C "$HOME/$prefix" -jcf "package.tar.bz2" .
