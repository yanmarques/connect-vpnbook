"""
Main module to open vpn connections.
"""


from util.filesystem import *
from util.network import on_secure_server, backup_server_on_failure, parse_html
from vpn_connector import open_connection, AuthError
from os import unlink


from dataclasses import dataclass, field
import traceback
import argparse
import pexpect
import os.path
import logging


VPNBOOK_URL = 'https://www.vpnbook.com/'
OCR_URL = 'https://smallseotools.com/image-to-text-converter/'
BKP_PWD_FILE = 'vpn_pwd.txt'
BKP_PWD_IMAGE = 'vpn_pwd.png'


def main(ovpn):
    """attempt to start a new OpenVPN connection from file"""
    # stop condition for file existence
    if not os.path.exists(ovpn):
        raise Exception('Ovpn file does not exist!')

    # stop condition for openvpn binary existence
    if not pexpect.run('which openvpn'):
        raise Exception("""Openvpn not seems to be installed! Quiting...""")

    cache_invalid = False
    attempts = 0
    checker = file_presence_checker()

    # execute maximum of 2 loops
    # the second loop may be only happen when the cached password is not valid
    # for authentication, so the new password must be retrieved.
    while attempts < 2:
        attempts += 1

        # condition, wheter cache is valid and file exist with non empty content
        if not cache_invalid and checker.hold_content_by_check(BKP_PWD_FILE):
            info('Using password on cache')
            password = checker.content
        else:
            password_url = retrieve_pwd_image()
            info('Retrieved passsword URL.')

            @backup_server_on_failure
            def recognise_image(session):
                """open a session with smallsetools to recognise the password"""

                # just knock server to catch some cookies, 1 req
                session.head(OCR_URL)

                # generate the parameters to image recognisation
                params = (('url', (None, password_url)), ('sub', (None, 'Converter')))

                # try to recognise the text in the image with ocr tool, 2 req
                hit_response = session.post(OCR_URL, files=params)

                # html-parser to get password by ID on page
                tagged_hit = parse_html(hit_response).find(id='hit')

                if tagged_hit is None:
                    raise Exception('Fail to recognise password')

                return tagged_hit.text.strip()

            def backup_pwd_image(session):
                """backup image re-using same connection pool"""

                # get image body with password, +1 req
                image_response = session.get(password_url)
                image_generator = image_response.iter_content(chunk_size=256)

                # + file operation
                filesave(BKP_PWD_IMAGE, image_generator)

            info('Attempting to recognize the password on image...')
            password = recognise_image(backup_pwd_image)

            # make backup of the password for further use
            # + file operation
            filesave(BKP_PWD_FILE, bytes(password, 'utf-8'))
            info('Recognition succeeded')

        info('Opening the vpn...')

        try:
            # stop condition, may fail to open connection
            process = open_connection(ovpn, password)
            info('Password is good, we are connected!')

            # attach the connection process to current process thread
            process.interact()

            # force condition to exit the loop
            attempts = 2
        except AuthError as e:
            # stop condition, authentication has failed with non cached password
            # put exception back on stack
            if checker.content is None:
                raise e

            # delete invalid cache
            os.unlink(BKP_PWD_FILE)

            # with the cache invalidated, a new attempt will be executed to
            # retrieve current password online
            cache_invalid = True

            # pretty print exception with the last exception from stack
            traceback.print_exc()
            error(f'{e.__class__.__name__}: {str(e)}')
            info('Attempting again to connect using image from vpnbook')
        info('Suceeded!')

def file_presence_checker():
    """helper function to hold content of file when exists"""
    @dataclass
    class content_holder():
        content: str = field(default=None)

        def hold_content_by_check(self, filename):
            if os.path.exists(filename):
                # + file operation
                content = getcontent(filename)
                if content is not None:
                    self.content = content
                    return True
    return content_holder()


@on_secure_server
def retrieve_pwd_image(session):
    """open a session with vpnbook to get generated image url"""
    # 1 req to vpnbook page content
    vpnbook_response = session.get(VPNBOOK_URL)

    # html-parser on previous content looking for the password image
    soap = parse_html(vpnbook_response)

    # stop condition
    # does the image is find and is not empty
    pwd_image = soap.find('img', src=lambda src: 'password.php' in src)
    if pwd_image is None or pwd_image is not None and not pwd_image.get('src'):
        raise Exception('Could not find password image!')

    return VPNBOOK_URL + pwd_image.get('src')


def info(text):
    """helper function to print an informational tag message"""
    logging.info(f'[*] {text}')


def error(text):
    """helper function to print an errored tag message"""
    logging.error(f'[-] {text}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(usage='%(prog)s [options] ovpn')
    parser.add_argument('ovpn', help='The ovpn file to open')

    # stop condition, when arguments are invalid
    arguments = parser.parse_args()

    try:
        main(arguments.ovpn)
    except KeyboardInterrupt:
        error('Interrupted by user!')
