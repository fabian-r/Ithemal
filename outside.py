#!/usr/bin/env python3

"""TODO document"""

from pathlib import Path

import rpyc

def unwrap_netref(o):
    if isinstance(o, dict):
        return { unwrap_netref(k): unwrap_netref(o[k]) for k in o }
    elif isinstance(o, list):
        return [ unwrap_netref(v) for v in o]
    else:
        return o

class RemoteLink:
    def __init__(self, hostname, port, sslpath, request_timeout):
        sslpath = Path(sslpath)
        self.hostname = hostname
        self.port = port
        self.certfile = str(sslpath / "cert.pem")
        self.keyfile = str(sslpath / "key.pem")
        self.request_timeout = request_timeout

        self.conn = None

    def __enter__(self):
        # self.conn = rpyc.ssl_connect(self.hostname,
        #         port=self.port,
        #         keyfile=self.keyfile,
        #         certfile=self.certfile,
        #         config={'sync_request_timeout': self.request_timeout},
        #         )
        self.conn = rpyc.connect(self.hostname,
                port=self.port,
                config={'sync_request_timeout': self.request_timeout},
                )
        return self

    def __exit__(self, exc_info, exc_value, trace):
        self.conn.close()
        return

    def run_ithemal(self, model_path, byte_str):
        assert self.conn is not None, "Connection must be open!"
        try:
            return unwrap_netref(self.conn.root.run_ithemal(model_path, byte_str))
        except rpyc.AsyncResultTimeout:
            return None


def main():
    import argparse

    rl = RemoteLink('127.0.0.1', port='42010', sslpath='./ssl', request_timeout=30)

    instr = b'\xbbo\x00\x00\x00dg\x90L\x0fNv@\xbb\xde\x00\x00\x00dg\x90'

    with rl:
        for mp in ['bhive/skl', 'paper/skl', 'bhive/ivb', 'paper/ivb', 'bhive/hsw', 'paper/hsw']:
            res = rl.run_ithemal(mp, instr)
            print("  {}: {}".format(mp, res))

if __name__ == '__main__':
    main()

