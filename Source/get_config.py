#! python3
""" Retrieve configuration from config.ini (located in parent folder to source code)

Checks that config.ini exists and has required fields
    [FreezerPro]
    username = 
    api_url = 

    [MailServer]
    smtpserver = 
    smtpport = 

    [System]
    support_email = 

Optional field:
    [System]
    email_support_only = True | False  # if true will only send emails to support_email address (default False)
    send_email_from = # default 'SamplePro <donotreply@scionresearch.com>'


Author: Wayne Schou
Date: August 2018

"""

import configparser
import os


def config_filename():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')


def get_config():
    configfile = config_filename()
    config = configparser.ConfigParser()
    if not os.path.exists(configfile):
        raise RuntimeError('Config file missing {}'.format(configfile))
    config.read(configfile)
    if 'FreezerPro' not in config:
        raise RuntimeError('{} does not contain section "FreezerPro"'.format(configfile))
    config_freezerpro = config['FreezerPro']
    if not config_freezerpro.get('Username'):
        raise RuntimeError('{} does not contain key "username" in section "FreezerPro"'.format(configfile))
    if not config_freezerpro.get('api_url'):
        raise RuntimeError('{} does not contain key "api_url" in section "FreezerPro"'.format(configfile))
    config_mailserver = config['MailServer']
    if not config_mailserver.get('smtpserver'):
        raise RuntimeError('{} does not contain key "smtpserver" in section "MailServer"'.format(configfile))
    if not config_mailserver.get('smtpport'):
        raise RuntimeError('{} does not contain key "smtpport" in section "MailServer"'.format(configfile))
    config_system = config['System']
    if not config_system.get('support_email'):
        raise RuntimeError('{} does not contain key "support_email" in section "System"'.format(configfile))
    return config

