from io import StringIO

import paramiko


class ExcecuteError(Exception):
    """
    Exception raised for errors if Paramiko
    ssh client excecute did not complete successfully

    Args:
        stdout -- standard output returned from ssh execute command
        stderr -- error returned from ssh terminal
    """

    def __init__(
        self, stdout="", stderr="Error executing ssh command",
        status=''
    ):
        message = f"""
        STDOUT: {stdout}
        STDERR: {stderr}
        STATUS: {status}
        """
        super().__init__(message)


class SshClient:
    """
    A wrapper of paramiko.SSHClient
    Created for reducing commands and to call
    sudo command when needed
    """
    TIMEOUT = 4

    def __init__(
        self, host, port, username, password, key=None, passphrase=None
    ):
        """
        Initializes and creates new ssh client
        """

        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key is not None:
            key = paramiko.RSAKey.from_private_key(
                StringIO(key), password=passphrase)
        self.client.connect(
            host, port, username=username, pkey=key,
            password=password, timeout=self.TIMEOUT,
            look_for_keys=False, allow_agent=False)

    def close(self):
        """
        Close client if it exists
        """
        if self.client is not None:
            self.client.close()
            self.client = None

    def file_exists(self, file_name: str):
        """
        Check if a file exists in server
        """
        command = f'test -e {file_name} && echo 1 || echo 0'
        stdout = self.execute(command)

        # Clean stdout
        stdout = stdout.strip('\n')  # Strips newlines
        stdout = stdout.strip()  # Strips spaces

        return True if stdout == '1' else False

    def execute(self, command, sudo=False, raise_exception=True) -> str:
        feed_password = False

        if sudo and self.username != "root":
            command = "sudo -S -p '' %s" % command
            feed_password = self.password is not None \
                and len(self.password) > 0

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
                raise ExcecuteError(
                    stdout=stdout, stderr=stderr, status=status)
            return stdout

        # Returns stdout, stderr, status
        return stdout, stderr, status


class Dir(object):
    """
    Simple object to keep track of present
    working directory when using Paramiko ssh client
    """

    def __init__(self, user: str) -> None:
        self.home = f'/home/{user}'
        self.pwd = self.home

    def cd(self, location: str = ''):
        """
        Change to a new directory
        """

        if location.startswith('/'):
            self.pwd = location
            return

        if self.pwd.endswith('/'):
            self.pwd += location
        else:
            self.pwd += f'/{location}'

    def get_cwd(self) -> str:
        return self.pwd

    def go_back(self):
        """
        Go one step back in this directory
        """

        directories = self.pwd.split('/')

        # Remove last element
        directories.pop()

        new_pwd = '/'.join(directories)
        self.pwd = new_pwd if new_pwd else '/'

    def __str__(self) -> str:
        return self.get_cwd()
