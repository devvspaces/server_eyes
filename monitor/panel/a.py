# class Person:
#     def __init__(self) -> None:
#         pass

#     def get_name(self):
#         print('Hi, there')


# per = Person()

# func = getattr(per, 'get_name', None)

# func()

# setattr(per, 'new_key', 'love')

# print(per.new_key)

import re
from typing import Dict, List

log = """

<VirtualHost *:80>
    ServerAdmin admin@site1.your_domain
    ServerName spacepen.tech

    DocumentRoot /home/team/spacepen.tech
    DirectoryIndex index.php index.html

    <Directory /home/team/spacepen.tech>
        Options Indexes FollowSymLinks MultiViews
        AllowOverride All
        Require all granted
    </Directory>

    <FilesMatch \.php$>
        SetHandler "proxy:unix:/var/run/php/php7.3-fpm.sock|fcgi://localhost"
    </FilesMatch>

    ErrorLog ${APACHE_LOG_DIR}/error.log
    AccessLog ${APACHE_LOG_DIR}/spacepen.log combined
    CustomLog${APACHE_LOG_DIR}/spacepen.log
    CustomLog /var/log/apache2/access.log combined
    CustomLog /var/log/apache2/agent_access.log agent
    AccessLog ${APACHE_LOG_DIR}/spacepen.log combined

    RewriteEngine on
    RewriteCond %{SERVER_NAME} =spacepen.tech
    RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>

"""



result :List[str] = re.findall(r'\w+ .*/.+.log', log)

results = []

apache_default_log_dir = '/var/log/apache2'
error_log_name = ''
access_log_name = ''

for item in result:
    try:
        key, value = item.split(' ')
        value = value.replace('${APACHE_LOG_DIR}', apache_default_log_dir)

        if not error_log_name and key == 'ErrorLog':
            error_log_name = value
            continue
    
        if not access_log_name and key == 'AccessLog':
            access_log_name = value
            continue

        log_dict = {
            'name': key,
            'location': value,
        }
        results.append(log_dict)

    except ValueError as e:
        pass

print(error_log_name)
print(access_log_name)
print(results)