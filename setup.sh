set -e -x
if [ -f env.in ] ; then
    eval echo "$(cat env.in)" > env
fi
virtualenv pyenv
curl -L "$url"| tar zx
