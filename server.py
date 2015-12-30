"""Github LaTeX builder.

Usage:
    server.py [-i HOST] [-p PORT]
    server.py --help
    server.py --version

Options:
    -h --help  Show this message.
    --version  Show the version.
    -i HOST    Hostname or IP to bind to [default: localhost].
    -p PORT    Port number [default: 9393].

"""
__version__ = '0.0.1'
from bottle import get, post, run, redirect, request, abort, HTTPResponse
from docopt import docopt
import os
import multiprocessing
import json
import builder


def validate_access_code():
    """If an access_code is provided, check whether it is valid. Return if yes, abort if not."""
    path = os.path.join(os.getcwd(), 'access_codes')
    access_code = request.GET.get('access_code')
    if access_code:
        if os.path.isfile(path):
            for line in open(path, 'r').xreadlines():
                code = line.split('#', 1)[0].strip('\n ')
                if code == access_code:
                    return
            abort(401, 'Unauthorized: Invalid access code.')
        abort(400, 'Bad request: Access code provided, but no access_code file present.')
    if os.path.isfile(path):
        abort(401, 'Unauthorized: Please provide an access code.')


@get('/')
def home():
    return '<img src="http://i1.kym-cdn.com/photos/images/newsfeed/000/345/309/5eb.gif">'


@post('/webhook')
def store():
    """Webhook for notifications about a new commit on Github."""
    validate_access_code()
    data = request.json

    if 'repository' in data:
        name = data['repository']['name']
        repo_url = data['repository']['ssh_url']
        commit = data['after']
        if data['ref'] is "refs/heads/master":
            b = builder.Builder(name, repo_url, commit)
            p = multiprocessing.Process(target=b.run)
            p.start()
            raise HTTPResponse('Started build process in background.\n', 202)
        else:
            raise HTTPResponse('Build process not started. I only build the master branch.')
    else:
        raise HTTPResponse('POST request did not contain a repo to build.\n', 400)



if __name__ == '__main__':
    args = docopt(__doc__, version=__version__)
    try:
        port = int(args['-p'])
    except ValueError:
        raise ValueError('Invalid port number: %s.' % args['-p'])
    run(host=args['-i'], port=port, debug=True)
