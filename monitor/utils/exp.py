import os, subprocess, shlex, re

os.chdir('C:\\Users\\Dell\\projects_eyes')

print(os.getcwd())

HTTPS_REMOTE_URL = 'https://n3trob3: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@github.com/n3trob3/laughing-funicular'

# command = f'git clone {HTTPS_REMOTE_URL}'
command = 'wsl'

# Split commands with shlex
commands = shlex.split(command)

# Call commands with subprocess
process = subprocess.run(commands, capture_output=True, text=True)
process.stdin = b'ls'

print(process.stdout)
print('*****************')
print(process.returncode)
print(process.stderr)

# process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# process.stdin = b'ls'

# print(process.stderr.read())
# print('*****************')
# print(process.returncode)
# print(process.stderr.read())

# os.system(command)

