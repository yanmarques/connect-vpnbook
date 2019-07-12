"""
This module provide functions to make/handle operations with network attributes.
"""


from bs4 import BeautifulSoup
from requests import Session
import secrets


def on_secure_server(command):
    """decorator function to start a command with a http session"""
    return lambda: run_server(command)


def run_server(command):
    """execute a command with newly session, with some configured headers"""

    # run command function with a "transparent" server
    with Session() as server:
        # set new headers for further connections
        server.headers.update({'User-Agent': get_random_ua(), 'DNT': '1'})
        return command(server)


def backup_server_on_failure(command):
    """decorator function to run a server with backup mechanism"""
    def backup_server(backup):
        return run_server(backup_on_failure(command)(backup))
    return backup_server


def backup_on_failure(command):
    """decorator function to execute a backup on any failure"""
    def with_backup(backup):
        def run_carefully(*args):
            try:
                return command(*args)
            except Exception as e:
                backup(*args)
                raise e
        return run_carefully
    return with_backup


def parse_html(response):
    """helper function to parse a response into a html soup"""
    return BeautifulSoup(response.text, 'html.parser')


def get_random_ua():
    """return a random user-agent string from file"""
    # stop condition, file does not exists, not readable...
    # + file operation
    with open('headers.txt') as hbuffer:
        all = hbuffer.readlines()
    return secrets.choice(all).strip()
