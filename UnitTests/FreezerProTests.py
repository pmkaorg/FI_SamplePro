
import requests
import json
API_URL = 'http://163.7.18.12/api'

#print(json.dumps({'method': 'freezers'}))
#r = requests.post("http://163.7.18.12/api",
#                  headers={'Content-Type': 'application/json'},
#                  data=json.dumps({'method': 'freezers'}),
#                  auth=('admin', 'admin'))

#data = r.json()
#print(json.dumps(data, indent=4, sort_keys=True))
#freezers = data['Freezers']
#print('Freezers =', data['Total'])
#print('Freezer fields', freezers[0].keys())
#for freezer in freezers:
#    print(freezer['name'])




#import requests
#import json

#options = {
#    'method': 'advanced_search',
#    'subject_type': 'Sample',
#    'query': [
#        {'field': 'sample_type_name',
#         'op': 'eq',
#         'value': 'Cell Line'},
#         #{'field': 'sample_group_name',
#         # 'op': 'contains',
#         # 'value': 'available for'},
#         #{'type': 'udf', 'field': 'Comments', 'op': 'contains', 'value': 'processed'}
#    ],
#    #'sdfs': ['id', 'locations_count', 'name', 'owner_username'],
#    #'udfs': ['']
#}


#r = requests.post("http://163.7.18.12/api",
#                  headers={'Content-Type': 'application/json'},
#                  data=json.dumps(options),
#                  auth=('admin', 'admin'))
#data = r.json()
#if data.get('error', None):
#    print(data['message'])
#else:
#    total = data['Total']
#    print(f'Samples found: {total}')
#    print(f"Samples returned {len(data['Samples'])}")
#    for sample in data['Samples']:
#        print(sample)


#r = requests.post(API_URL,
#                  data = {'method': 'sample_info',
#                          'id': '100337',
#                          },
#                  auth=('admin', 'admin'))
#data = r.json()
#print(data)

#import re
#r = requests.post(API_URL,
#                  data = {'method': 'audit',
#                          'date_flag': '20/7/2018,1/8/2018',
#                          'limit': 1000,  #1000 is maximum that can be returned
#                          },
#                  auth=('admin', 'admin'))
#data = r.json()
#if (data['Total'] != len(data['AuditRec'])):
#    print('All records not returned')
#    print('Total=', data['Total'], 'Returned=', len(data['AuditRec']))
#audits = data['AuditRec']
##for audit in audits:
##    print(audit)
##obj_names = set([audit['obj_name'] for audit in audits])
##print(obj_names)
#states = ['Store Request', 'Retrieve Request', 'Dispose Request']
#mm = [audit for audit in audits if audit['obj_name'] in states]
#state_changes = [{'type': audit['obj_name'], 
#                  'date': audit['created_at'],
#                  'user_name': audit['user_name'],
#                  'message': audit['message'],  
#                  'comments': audit['comments']} 
#                 for audit in audits if audit['obj_name'] in states]
##extract sample_id from message
#for m in state_changes:
#    pattern = '(.*) ID: <u>(\w+)</u>(.*)'
#    match = re.match(pattern, m['message'])
#    m['sample_id'] = match.groups()[1]
#    print(m['date'], m['type'], 'for sample', m['sample_id'], 'by', m['user_name'])


#import requests
#import json

#r = requests.post("http://163.7.18.12/api",
#                  data={'method': 'vials_sample',
#                        'sample_id': 112741},
#                  auth=('admin', 'admin'))

#data = r.json()
## print(json.dumps(data, indent=4, sort_keys=True))
#locations = data['Locations']
#print('Locations =', data['Total'])
#print('Location fields', locations[0].keys())
#for location in locations:
#    print(location['state_color'], location['state_info'])



#import requests
#import json

#r = requests.post("http://163.7.18.12/api",
#                  data={'method': 'vials_sample',
#                        'vial_state_type_id': 1},
#                  auth=('admin', 'admin'))

#data = r.json()
#print(json.dumps(data, indent=4, sort_keys=True))
#locations = data['Locations']
#print('Locations =', data['Total'])
## print('Location fields', locations[0].keys())
#print('location_id', 'sample_id', 'barcode')
#for location in locations:
#    print(location['loc_id'], location['sample_id'], location['barcode_tag'])



#import requests
#import json

#r = requests.post("http://163.7.18.12/api",
#                  data={'method': 'users'},
#                  auth=('admin', 'admin'))

#data = r.json()
#print(json.dumps(data, indent=4, sort_keys=True))






#import requests
#import json

#r = requests.post("http://163.7.18.12/api",
#                  data={'method': 'user_groups' },
#                  auth=('admin', 'admin'))

#data = r.json()
##print(json.dumps(data, indent=4, sort_keys=True))
#groups = data['Groups']
#print('Groups: ', [group['name'] for group in groups])
#print()
#biotransformation_group = next((group for group in groups if group['name'] == 'Biotransformation'))
#biotransformation_users = biotransformation_group['users']
#print('Biotransformation Group Users: ', biotransformation_users)
#print()

#r = requests.post("http://163.7.18.12/api",
#                  data={'method': 'users'},
#                  auth=('admin', 'admin'))

#data = r.json()
##print(json.dumps(data, indent=4, sort_keys=True))
#users = data['Users']
#bio_ids = [group_user['id'] for group_user in biotransformation_users]
#bio_users = [(user['username'], user['email']) for user in users if user['id'] in bio_ids]
#print('Email:', bio_users)



#r = requests.post("http://163.7.18.12/api",
#                    data={'method': 'gen_token' },
#                    auth=('admin', 'admin'))
#data = r.json()
##print(json.dumps(data, indent=4, sort_keys=True))
#auth_token = data['auth_token']
#print('Authentication token', auth_token)

import smtplib
from email.mime.text import MIMEText
SMTPServer = '163.7.18.150'
SMTPPort = 25
title = 'My title'
msg_content = '<h2>{title} &rarr; <font color="green">OK</font></h2>\n'.format(title=title)
message = MIMEText(msg_content, 'html')

message['From'] = 'Sample Management System'
message['To'] = 'Wayne'
message['Subject'] = 'Test HTML'

msg_full = message.as_string()

server = smtplib.SMTP(SMTPServer, SMTPPort)
server.starttls()
#server.login('sender@server.com', 'senderpassword')
server.sendmail("DoNotReply@scionresearch.com",
                ['wayne.schou@scionresearch.com'],
                msg_full)
server.quit()