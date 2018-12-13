import configparser
import get_config

#API_URL = 'https://freezerpro.scionresearch.com/api'  # Production database
##API_URL = 'http://163.7.18.12/api' #Training database
#USER_NAME = 'Schouw'  #case-sensitive
#SMTPServer = '163.7.18.150'
#SMTPPort = 25
#SUPPORT_EMAIL = 'jenny.simpson@scionresearch.com' #'wayne.schou@scionresearch.com'  #

config = configparser.ConfigParser()
config['FreezerPro'] = {}
config['FreezerPro']['Username'] = 'FreezerLDAP'
#config['FreezerPro']['API_URL'] = 'http://163.7.18.12/api' #Training database
config['FreezerPro']['API_URL'] = 'https://freezerpro.scionresearch.com/api'  # Production database
config['MailServer'] = {}
config['MailServer']['SMTPServer'] = '163.7.18.150'
config['MailServer']['SMTPPort'] = '25'
config['System'] = {}
config['System']['Support_Email'] = 'jenny.simpson@scionresearch.com'

filename = get_config.config_filename()
with open(filename, 'w') as configfile:
    config.write(configfile)

