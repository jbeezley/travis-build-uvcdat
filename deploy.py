import os
import sys
import json

import pip
pip.main(['install', 'requests', 'PyYAML'])

import requests
from yaml import load

if os.environ.get('TRAVIS_SECURE_ENV_VARS') == 'false':
    print('Cannot deploy without secure variables')
    sys.exit(0)

travis = load(open('.travis.yml').read())
apt = travis.get('addons', {}).get('apt', {}).get('packages', [])
home = os.path.expanduser('~')
name = os.environ['name']
version = os.environ['version']
url = os.environ['url']
prefix = os.path.join(home, os.environ['prefix'])
env = [l.strip() for l in open('env').readlines() if l.strip()]

girder_url = os.environ['GIRDER_URL'].rstrip('/')
girder_user = os.environ['GIRDER_USER']
girder_password = os.environ['GIRDER_PASSWORD']
girder_folder = os.environ['GIRDER_FOLDER']

depends = [
    d.strip() for d in os.environ.get('PACKAGE_DEPENDS', '').split(':') if d.strip()
]

chunk_size = 1024 * 1024 * 64

token = requests.get(
    girder_url + '/user/authentication',
    auth=(girder_user, girder_password)
).json()['authToken']['token']

item = requests.post(
    girder_url + '/item',
    params={
        'token': token,
        'folderId': girder_folder,
        'name': name + ' ' + version
    }
).json()['_id']

assert requests.put(
    girder_url + '/item/' + item + '/metadata',
    params={'token': token},
    data=json.dumps({
        'name': name,
        'version': version,
        'source': url,
        'prefix': prefix,
        'repo': os.environ.get('TRAVIS_REPO_SLUG'),
        'head': os.environ.get('TRAVIS_COMMIT'),
        'job_number': os.environ.get('TRAVIS_JOB_NUMBER'),
        'os': os.environ.get('TRAVIS_OS_NAME'),
        'apt': apt,
        'depends': depends
    })
).ok

with open('package.tar.bz2') as f:
    size = os.path.getsize('package.tar.bz2')

    id = requests.post(
        girder_url + '/file',
        params={
            'token': token,
            'parentType': 'item',
            'parentId': item,
            'name': name + '_' + version + '.tar.bz2',
            'size': size
        }
    ).json()['_id']

    print('Uploading file ' + id)

    next_size = min(chunk_size, size)
    while next_size > 0:
        offset = f.tell()
        chunk = f.read(next_size)

        print(
            'Uploading ' + str(next_size) + ' bytes at ' + str(offset)
        )
        r = requests.post(
            girder_url + '/file/chunk',
            params={
                'token': token,
                'offset': offset,
                'uploadId': id
            },
            files={
                'chunk': chunk
            }
        )

        if not r.ok:
            raise Exception(r.content.encode('utf-8'))

        next_size = min(chunk_size, size - f.tell())
