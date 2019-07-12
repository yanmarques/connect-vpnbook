"""
This module provide tools to open interactive OpenVPN connections.
"""


import pexpect
import getpass


class AuthError(Exception):
    """exception class for general authentication error"""
    def __init__(self, message='Authentication failed!'):
        super().__init__(message)


class VPNConnector():
    """class to open openvpn connections from command line interpreter, with
    built-in backup mechanism"""
    DEFAULT_USERNAME = 'vpnbook'

    def __init__(self, ovpn, password):
        self.ovpn = ovpn
        self.password = password

    def open_connection(self):
        # system process root call to open vpn
        process = pexpect.spawn(f'sudo openvpn {self.ovpn}')

        first_expectations = ['.*password.*', 'Enter Auth Username:']

        # keep prompting password till it's valid
        while process.expect(first_expectations) == 0:
            process.sendline(getpass.getpass())

        # authentication process
        process.sendline(VPNConnector.DEFAULT_USERNAME)

        # stop condition, expect to enter password
        process.expect('Enter Auth Password:')
        process.sendline(self.password)

        decision_expectations = ['AUTH_FAILED', 'Initialization Sequence Completed',
            pexpect.EOF]

        # handle authentecation execution seeking to errors
        response = process.expect(decision_expectations)

        # stop condition when auth has failed
        if response == 0:
            raise AuthError()
        # stop condition when process just exited
        if response == 2:
            print(process.before)
            raise Exception('Unexpected process exit. Is vpn already up?')
        return process
