import os, subprocess, shlex, re

def get_enabled_sites():

    # Check if the server is 'posix'
    name = os.name
    if name == 'nt':

        return [{'file_name': 'kogi.conf', 'log': 'kogi.log', 'url': 'kogi.spacepen.tech'}, {'file_name': 'kogi_test.conf', 'log': 'kogi_test.log', 'url': 'kogi_test.spacepen.tech'}, {'file_name': 'monitor.conf', 'log': 'monitor.log', 'url': 'epanel.spacepen.tech'}, {'file_name': 'ondo_farmers.conf', 'log': 'ondo_farmers.log', 'url': 'odk.spacepen.tech'}, {'file_name': 'site1.conf', 'log': 'spacepen.log', 'url': 'spacepen.tech'}]


    apache_path = '/etc/apache2/sites-enabled/'
    command = f'ls {apache_path}'

    # Split commands with shlex
    commands = shlex.split(command)

    # Call commands with subprocess
    process = subprocess.run(commands, capture_output=True, text=True)

    try:

        # Get the result
        result = process.stdout

        # Use regex to filter out result
        results = re.findall(r'.+.conf', result)

        # Remove ssl configurations
        file_names = [i for i in results if 'le-ssl' not in i]

        # Set the results down
        results_list = []

        # Loop through file results
        for file in file_names:
            # Open file conf in result and parse out ServerName and Log file name
            command = f'cat {apache_path}{file}'

            # Split commands with shlex
            commands = shlex.split(command)

            # Call commands with subprocess
            process = subprocess.run(commands, capture_output=True, text=True)

            # Get the contents of the file
            text = process.stdout

            # Use regex to get the log name
            result = re.search(r'/.+.log', text)
            log_name = result.group().lstrip("/")

            # Re to match server name line in to groups
            result = re.search(r'(ServerName)\s(.*)', text)

            # Get the group for the values of server name line
            urls_ips = result.groups()[1]

            # Get ips in the value from urls_ips
            ips = re.findall( r'[0-9]+(?:\.[0-9]+){3}', urls_ips)
            
            # Remove ips from the list
            urls_ips = urls_ips.split()

            for i in ips:
                urls_ips.remove(i)
            
            # Get one link out of urls_ips
            link = urls_ips[0]

            
            # Arrange data in a dict and append to results_list
            data = {
                'file_name': file,
                'log': log_name,
                'url': link,
            }

            results_list.append(data)


        return results_list

    except Exception as e:
        print(f'Error while trying to get directory list for {apache_path}')

    return ''


if __name__ == '__main__':
    print(get_enabled_sites())