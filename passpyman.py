#! /bin/env python3

import os
import sys
import string
import random
import argparse
import configparser
import pprint


PASS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'passes.ini'))

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

    args = parser.parse_args()

    print(args)
    if args.password:
        print(gen_secret())
    elif args.list_sections:
        print(get_passes())
    else:
        parser.print_help()
