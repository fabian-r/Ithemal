#!/usr/bin/env python3

"""TODO document"""


import os
from pathlib import Path
import re
import subprocess

from tempfile import NamedTemporaryFile

import rpyc
from rpyc.utils.authenticators import SSLAuthenticator
from rpyc.utils.server import ThreadedServer


def run_experiment(model_path, byte_str):

    with NamedTemporaryFile(mode='wb', suffix='.o', prefix='current_bmk_') as f:
        bmk_file_name = f.name

        command = [
            "python", "/home/ithemal/ithemal/learning/pytorch/ithemal/predict.py",
            "--model", "/home/ithemal/ithemal/models/{model_path}.dump".format(model_path=model_path),
            "--model-data", "/home/ithemal/ithemal/models/{model_path}.mdl".format(model_path=model_path),
            "--file", bmk_file_name,
            ]

        f.write(byte_str)
        f.flush()

        rv = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if rv.returncode != 0:
        print('  execution failed!')
        return { 'TP': None, 'error': "execution failed\nstdout:\n" + rv.stdout.decode('utf-8') + "\nstderr:\n" + rv.stderr.decode('utf-8') }

    str_res = rv.stdout.decode("utf-8")

    m = re.search(r"(\d+\.\d+)", str_res)
    if m is None:
        return { 'TP': None, 'error': "throughput missing in ithemal output" }

    total_cycles = float(m.group(1))
    total_cycles = total_cycles / 100.0
    return {'TP': total_cycles}

_allowed_model_paths = [
        'bhive/skl',
        'bhive/ivb',
        'bhive/hsw',
        'paper/skl',
        'paper/ivb',
        'paper/hsw',
    ]

class MyService(rpyc.Service):
    def __init__(self):
        pass

    def on_connect(self, conn):
        print("Opened connection")

    def on_disconnect(self, conn):
        print("Closed connection")

    def exposed_run_ithemal(self, model_path, byte_str):
        print("handling request for running ithemal")
        res = run_experiment(model_path=model_path, byte_str=byte_str)
        return res

def create_certs(self, sslpath='./ssl/'):
    """Create a self-signed certificate without password that is valid for
    (roughly) 10 years.
    """

    sslpath = Path(sslpath)

    os.makedirs(sslpath)

    subprocess.call([
            'openssl',
            'req',
            '-new',
            '-x509',
            '-days', '3650',
            '-nodes',
            '-out', sslpath / 'cert.pem',
            '-keyout', sslpath / 'key.pem',
        ])
    with open(sslpath / 'ca_certs.pem', 'w') as f:
        f.write('#TODO fill this\n\n')

def main():
    import argparse

    default_ssl_path = Path(__file__).parent / 'ssl'

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('-p', '--port', metavar='PORT', type=int, default="42010",
                      help='the port to listen for requests')
    ap.add_argument('--sslpath', metavar='PATH', default=str(default_ssl_path),
                      help='the path to a folder containing an SSL key, certificate and ca file')
    args = ap.parse_args()

    sslpath = Path(args.sslpath)

    if not sslpath.is_dir():
        create_certs(sslpath)

    certfile = sslpath / "cert.pem"
    keyfile = sslpath / "key.pem"
    ca_certs = sslpath / "ca_certs.pem"

    for f in (certfile, keyfile, ca_certs):
        if not f.is_file():
            raise RuntimeError("SSL file missing: {}".format(f))

    # authenticator = SSLAuthenticator(keyfile=keyfile, certfile=certfile, ca_certs=ca_certs)
    authenticator = None

    service = MyService()

    t = ThreadedServer(service, port=args.port, authenticator=authenticator)
    print("Starting server")
    t.start()


if __name__ == '__main__':
    main()

