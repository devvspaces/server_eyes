import paramiko
from io import StringIO
from typing import Tuple


class ExcecuteError(Exception):
    """Exception raised for errors if Paramiko ssh client excecute did not complete successfully

    Attributes:
        stdout -- standard output returned from ssh execute command
        stderr -- error returned from ssh terminal
    """

    def __init__(self, stdout="", stderr="Error executing ssh command", status=''):
        message = f"\nSTDOUT: {stdout}\nSTDERR: {stderr}\nSTATUS: {status}\n\n"
        super().__init__(message)

        

class SshClient:
    "A wrapper of paramiko.SSHClient"
    TIMEOUT = 4

    def __init__(self, host, port, username, password, key=None, passphrase=None):
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key is not None:
            key = paramiko.RSAKey.from_private_key(StringIO(key), password=passphrase)
        self.client.connect(host, port, username=username, password=password, pkey=key, timeout=self.TIMEOUT)

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
    
    def file_exists(self, file_name:str):
        command = f'test -e {file_name} && echo 1 || echo 0'
        stdout = self.execute(command)

        # Clean stdout
        stdout = stdout.strip('\n') # Strips newlines
        stdout = stdout.strip() # Strips spaces

        return True if stdout == '1' else False

    def execute(self, command, sudo=False, raise_exception=True) -> str:
        feed_password = False

        if sudo and self.username != "root":
            command = "sudo -S -p '' %s" % command
            feed_password = self.password is not None and len(self.password) > 0

        stdin, stdout, stderr = self.client.exec_command(command)

        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        
        # Get stdout, status
        status = stdout.channel.recv_exit_status()
        stderr = stderr.read().decode()
        stdout = stdout.read().decode()
        
        if raise_exception:
            if status != 0:
                raise ExcecuteError(stdout=stdout, stderr=stderr, status=status)
            return stdout

        # Returns stdout, stderr, status
        return stdout, stderr, status


class Dir(object):
    """Simple object to keep track of present working directory when using Paramiko ssh client"""
    def __init__(self, user:str) -> None:
        self.home = f'/home/{user}'
        self.pwd = self.home
    
    def cd(self, location:str=''):

        if location.startswith('/'):
            self.pwd = location
            return
        
        if self.pwd.endswith('/'):
            self.pwd += location
        else:
            self.pwd += f'/{location}'
    
    def go_back(self):
        directories = self.pwd.split('/')

        # Remove last element
        directories.pop()

        new_pwd = '/'.join(directories)
        self.pwd = new_pwd if new_pwd else '/'
    
    def __str__(self) -> str:
        return self.pwd