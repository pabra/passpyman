#! /bin/env python3

import os
import io
import sys
import string
import random
import argparse
import configparser
import pprint

from os.path import join as pjoin
from os.path import isdir
from os.path import isfile

# output = io.StringIO()
# output.write('First line.\n')
# contents = output.getvalue()
PASS_FILE   = os.path.abspath(os.path.join(os.path.dirname(__file__), 'passes.ini'))
HOME_DIR    = os.getenv('HOME')
CONFIG_DIR  = pjoin(HOME_DIR, '.config', 'passpyman')
CONFIG_FILE = pjoin(CONFIG_DIR, 'passpyman.ini')

def info(*msg):
    print(*msg)

def setup():
    assert HOME_DIR, 'missing HOME_DIR'
    if not isdir(CONFIG_DIR):
        checked_parts = ['/']
        path_parts = [d for d in CONFIG_DIR.split(os.path.sep) if d]
        path_parts = CONFIG_DIR.split(os.path.sep)
        for p in path_parts:
            checked_parts.append(p)
            path = pjoin(*checked_parts)
            if not isdir(path):
                info('make dir:', path)
                os.mkdir(path)

    if not isfile(CONFIG_FILE):
        conf = configparser.ConfigParser()
        conf.add_section('Config')
        conf.set('Config', 'password_file', 'pass.gpg')
        with open(CONFIG_FILE, 'w') as fp:
            conf.write(fp)

def get_passes():
    cp = configparser.ConfigParser()
    cp.read(PASS_FILE)

    return sorted(cp.sections())

def gen_secret(len=15):
    "Return good random string of A-Za-z0-9 which never starts with a digit."
    required_groups = (string.ascii_lowercase,
                       string.ascii_uppercase,
                       string.digits,
                       '_-#~+?')

    char_list = list(''.join(required_groups))
    random.shuffle(char_list)

    def test_occurence(s):
        group_count = {}
        for rg in required_groups:
            group_count[rg] = 0
            for c in rg:
                group_count[rg] += s.count(c)

        return all(2 <= v for k, v in group_count.items())

    s = ''
    while not s or s[:1] not in string.ascii_lowercase or not test_occurence(s):
        s = ''.join(random.SystemRandom().choice(''.join(char_list))
                    for _ in range(len))

    return s

if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()

    pa = parser.add_argument
    ga = group.add_argument

    ga('-p', '--password', action='store_true', help='generate password')
    ga('-l', '--list-sections', action='store_true', help='list all section entries')
    ga('-s', '--setup', action='store_true', help='initial setup')

    args = parser.parse_args()

    if args.password:
        print(gen_secret())
    elif args.list_sections:
        print(get_passes())
    elif args.setup:
        setup()
    else:
        parser.print_help()
