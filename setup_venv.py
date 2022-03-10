import subprocess, sys, shlex
from pathlib import Path


# get the name for the virtual enviroment
env = sys.argv[1]

# Setting the requirements txt location
try:
    REQUIREMENT = sys.argv[2]
except IndexError:
    REQUIREMENT = 'requirements.txt'

# Get python location
process = subprocess.run(shlex.split('which python3'), capture_output=True, text=True)

if process.returncode != 0:
    raise OSError('Sorry python3 is not installed')

python_location = process.stdout.strip()

# Create the virtual enviroment
process = subprocess.run(shlex.split(f'{python_location} -m venv {env}'), capture_output=True)

if process.returncode == 0:
    print(f"Successfully created virtual enviroment {env}")

    pip_bin = f'{env}/bin/pip3'

    # Check if REQUIREMENT file existed
    if Path(REQUIREMENT).exists():
        # Install requirements.txt
        process = subprocess.run(shlex.split(f'{pip_bin} install -r {REQUIREMENT}'), capture_output=True, text=True)

        if process.returncode == 0:
            print('Installed packages in requirements.txt')

            print(process.stdout)

            print(f'Process completed! Now activate your environment with "source {env}/bin/activate"')
        
        else:
            print('Error while installing packages')
            print(process.stderr)
    
    else:
        print(f"{REQUIREMENT} file does not exist")

else:
    print('Error while creating virtual enviroment')
    print(process.stderr)





