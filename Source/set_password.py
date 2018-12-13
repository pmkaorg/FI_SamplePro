import keyring
import getpass
import get_config

# saves the password of the FreezeroPro API user in Windows Credential Locker
# ensure username (2nd parameter) is valid username
# password will be requested when run

config = get_config.get_config()

USER_NAME = config['FreezerPro']['Username']

print('Store the password for FreezerPro API access user {}'.format(USER_NAME))
keyring.set_password('FreezerPro', USER_NAME, getpass.getpass())


