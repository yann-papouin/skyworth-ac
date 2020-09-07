#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 2020-07-25 15:50

# Python 3 compatibility
from builtins import (input, str)

# Python 3 compatibility
try:
    input = raw_input
except NameError:
    pass

import argparse
import collections
import logging
import os
import re
import subprocess
import sys
from builtins import IndexError

from colorama import Back, Fore, Style

try:
    from natsort import natsorted
except:
    natsorted = sorted

logger = logging.getLogger(__name__)

ACTIONS = {}
TITLE = 'Menu'
INPUT_PREFIX = ''

pre_action_fn = None
post_action_fn = None
last_choice = None


# Clear console
def clear():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


# Exit program
def exit():
    sys.exit(0)


# Restart program
def restart():
    python = sys.executable
    os.execl(python, python, *sys.argv)


# Main menu
def main_menu(actions, wait=False):
    if wait:
        print("Press return to continue.\n")
        input("")
    clear()

    print(Back.WHITE + Fore.BLACK)
    print(TITLE)
    print(Style.RESET_ALL)
    print_actions(actions)

    try:
        choice = input("\n {0}>>  ".format(INPUT_PREFIX))
        exec_menu(actions, choice)
        # Recreate menu from ACTIONS if an updated is needed
        main_menu(actions=ACTIONS, wait=True)
    except KeyboardInterrupt as e:
        print("\n")
        exit()


def print_actions(actions):
    global last_choice
    keylist = natsorted([k for k, v in actions.items()])
    for k in keylist:
        if len(actions[k]) > 2:
            indent = actions[k][2]
        else:
            indent = 0

        if len(actions[k]) > 3:
            prefix = actions[k][3]
        else:
            prefix = False

        if len(actions[k]) > 4:
            suffix = actions[k][4]
        else:
            suffix = False

        if prefix:
            print(prefix)

        description = actions[k][0]
        if k == last_choice:
            description = '* ' + description

        print('  {0}. {1}'.format(k.rjust(3 + indent), description))

        if suffix:
            print(suffix)


def exec_action(name, choice, actions=None):
    ch = str(choice)
    if actions is None:
        actions = ACTIONS
    if name == 'pre':
        global pre_action_fn
        if pre_action_fn is not None:
            pre_action_fn(ch, actions[ch][0])
    if name == 'post':
        global post_action_fn
        if post_action_fn is not None:
            post_action_fn(ch, actions[ch][0])


def exec_menu(actions, choice, cli=False):
    if not cli:
        clear()
    fn = None
    ch = str(choice)
    if ch == '':
        pass
    else:
        try:
            print(Fore.GREEN)
            print("Execute: {0}".format(actions[ch][0]))
            print(Style.RESET_ALL)
            fn = actions[ch][1]
        except (KeyError, IndexError) as e:
            if cli:
                print(
                    "{0} is not a valid argument, possible values are:".
                    format(ch)
                )
                print_actions(actions)
            else:
                print("Invalid selection, please try again.\n")
        if fn is not None:
            exec_action('pre', choice, actions)
            fn()
            exec_action('post', choice, actions)
    return


def show_menu(parse_args=False):
    if parse_args and len(sys.argv) > 1:
        exec_menu(ACTIONS, sys.argv[1], cli=True)
    else:
        # Launch main menu
        main_menu(actions=ACTIONS)


# Main Program
if __name__ == "__main__":
    show_menu(parse_args=True)
