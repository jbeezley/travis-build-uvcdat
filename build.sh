set -e -x
mkdir "${buildpath}"
pushd "${buildpath}"
cmake ${cmake_opts} "-DCMAKE_INSTALL_PREFIX=$HOME/$prefix" "../$srcpath"
make &
while ps -p $! >&-; do
    sleep 60
    echo "Ping!"
done
popd
