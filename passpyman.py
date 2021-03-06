#! /bin/env python2
# -*- coding: utf-8 -*-

import os
import re
import sys
import string
import random
import argparse
import pprint

from StringIO       import StringIO
from ConfigParser   import SafeConfigParser
from subprocess     import call, Popen, PIPE
from getpass        import getpass
from os.path        import join as pjoin
from os.path        import isdir
from os.path        import isfile

HOME_DIR    = os.getenv('HOME')
CONFIG_DIR  = pjoin(HOME_DIR, '.config', 'passpyman')
CONFIG_FILE = pjoin(CONFIG_DIR, 'passpyman.ini')

GPG_SECRET  = "123qwe"

def info(*msg):
    print ' '.join(msg)

def error(*msg):
    info(*msg)
    sys.exit(1)

def asint(int_str, default=None):
    try:
        return int(int_str)
    except:
        return default

def choose(max=None, min=1):
    assert max, 'missing max'
    assert isinstance(min, (int, long)), 'min must be int'
    assert isinstance(max, (int, long)), 'max must be int'
    assert max >= min, 'max must be >= min'
    inp = ''
    while not min <= inp <= max:
        inp = asint(raw_input('[%s-%s]: ' % (min, max)))

    return inp

def choose_from_list(choose_list=[]):
    list_len = len(choose_list)
    list_str_len = len(str(list_len))
    tpl = '%%-%ss %%s' % list_str_len
    for i, x in enumerate(choose_list):
        info(tpl % (i+1, x))

    return choose_list[choose(list_len) - 1]

def setup():
    assert HOME_DIR, 'missing HOME_DIR'
    sect = 'Config'
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
        conf = SafeConfigParser()
        conf.add_section(sect)
        conf.set(sect, 'password_file', 'pass.gpg')
        with open(CONFIG_FILE, 'w') as fp:
            conf.write(fp)

def test_which(cmd):
    "Test if proc is available."
    if call('which %s' % cmd, shell=True, stdout=PIPE, stderr=PIPE):
        error('command not found:', cmd)

def get_gpg_secret():
    return GPG_SECRET

def gpg_encrypt(txt, sec):
    test_which('gpg')
    gpg = Popen(['gpg', '--batch', '-c', '--passphrase', sec, '-o', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out = gpg.communicate(input=txt)[0]
    return out

def gpg_decrypt(txt, sec):
    test_which('gpg')
    gpg = Popen(['gpg', '--batch', '-d', '--passphrase', sec, '-o', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out = gpg.communicate(input=txt)[0]
    if gpg.returncode != 0:
        raise ValueError("gpg failed")
    return out

def get_config():
    cp = SafeConfigParser()
    cp.read(CONFIG_FILE)

    return cp

def get_password_file_name():
    sect = 'Config'
    conf = get_config()
    if not sect in conf.sections():
        return None

    if not 'password_file' in conf.options(sect):
        return None

    pass_file_name = conf.get(sect, 'password_file')

    if pass_file_name:
        return pjoin(CONFIG_DIR, pass_file_name)

    else:
        return None

def write_password_file(cp):
    pass_file = get_password_file_name()
    buf = StringIO()
    cp.write(buf)
    buf.flush()

    with open(pass_file, 'w') as fd:
        fd.write(gpg_encrypt(buf.getvalue(), get_gpg_secret()))

def read_password_file():
    pass_file = get_password_file_name()

    assert pass_file, 'no pass file'

    if not isfile(pass_file):
        return ''

    with open(pass_file, 'r') as fd:
        return gpg_decrypt(fd.read(), get_gpg_secret())

def get_passwords():
    pass_txt = read_password_file()
    buf = StringIO(pass_txt)
    cp = SafeConfigParser()
    cp.readfp(buf)
    buf.close()

    return cp

def get_password_sections():
    return sorted(get_passwords().sections())

def add_pass(section=None):
    if not section:
        section = raw_input('Section: ')
    pw = get_passwords()
    assert section not in pw.sections(), 'section already exists: %r' % section

    user = raw_input('Username: ')
    passwd = getpass('Password: ')
    assert passwd, 'no password given'
    pw.add_section(section)
    pw.set(section, 'user', user)
    pw.set(section, 'pass', passwd)
    write_password_file(pw)

def get_section_content(section):
    pw = get_passwords()
    assert section in pw.sections(), 'section does not exist: %r' % section

    return dict(pw.items(section, raw=True))

def print_section_content(section):
    pprint.pprint(get_section_content(section))

def gen_secret(len=15):
    "Return good random string which never starts with a digit."
    required_groups = (string.ascii_lowercase,
                       string.ascii_uppercase,
                       string.digits,
                       '._-#~+?')

    char_list = list(''.join(required_groups))
    random.shuffle(char_list)

    def test_occurence(s):
        group_count = {}
        for rg in required_groups:
            group_count[rg] = 0
            for c in rg:
                group_count[rg] += s.count(c)

        return (# at least 2 chars of each group
                all(2 <= v for k, v in group_count.items())
                # no char followed by itself
                and not re.search(r'(.)\1', s)
                # no char more than twice in string
                and not re.search(r'(.).*\1.*\1', s))

    s = ''
    while not s or s[:1] not in string.ascii_lowercase or not test_occurence(s):
        s = ''.join(random.SystemRandom().choice(''.join(char_list))
                    for _ in range(len))

    return s

if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    # group = parser.add_mutually_exclusive_group()

    pa = parser.add_argument
    # ga = group.add_argument

    pa('action', choices=['add', 'get', 'set', 'pass', 'setup'], help='main action')
    pa('-s', '--section', help='name of the section')
    pa('-u', '--user', help='user name')
    pa('-p', '--pass', help='password')
    # ga('-p', '--password', action='store_true', help='generate password')
    # # ga('-p', '--password', action='store_true', nargs='?', default=None, help='generate password')
    # ga('-l', '--list-sections', action='store_true', help='list all section entries')
    # ga('-a', '--add', dest='section', help='add new section')
    # ga('-s', '--setup', action='store_true', help='initial setup')

    args = parser.parse_args()
    print args

    if 'add' == args.action:
        print 'action:', args.action
        add_pass(section=args.section)

    elif 'get' == args.action:
        print 'action:', args.action
        if not args.section:
            info('\n'.join(get_password_sections()))
        else:
            print_section_content(args.section)

    elif 'set' == args.action:
        print 'action:', args.action

    elif 'pass' == args.action:
        print 'action:', args.action
        print gen_secret()

    elif 'setup' == args.action:
        setup()

    else:
        parser.print_help()
