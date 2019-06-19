#! python3
"""FreezerPro API requests for the Sample Management System
Author: Wayne Schou
Date: August 2018

Constants:
   There are a number of constants defined at the top of the file that should be setup correctly
   API_URL: url of freezerpro system
   USER_NAME: username to use to log into freezerpro
   SMTPServer: ip address of SMTP server
   SMTPPort: port of SMTP server
   SUPPORT_EMAIL: email address to send any exceptions to.

Security:
    The module uses package keyring to safely hold the password for user_name (stored under service=FreezerPro)
    On Windows this will use the Windows Credential Locker
    The password can be set or updated for the user in one of three ways:
    1. Run set_password.py (setting appropriate user_name)
    2. Run commandline utility keyring (installed in python Scripts folder) e.g. keyring set FreezerPro admin
    3. Run keyring module e.g. python -m keyring set FreezerPro admin

    The module requests an authorization token (will omit multiple "API Session Created" and "API Session Removed" entries in the audit log)
    The autorization token is only valid for 10 minutes after generation or last use.
"""

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import json
from enum import IntEnum, unique
import smtplib
from email.mime.text import MIMEText
import keyring
from datetime import datetime, date, timedelta
import re
import traceback
import pandas as pd
import get_config

try:
    config = get_config.get_config()
except RuntimeError as err:
    # ultimate fallback when config.ini not correct
    s = smtplib.SMTP('163.7.18.150', 25)
    SUPPORT_EMAIL = 'wayne.schou@scionresearch.com'
    msg = "From: SamplePro <donotreply@scionresearch.com>\r\n"\
          "To: {}\r\n"\
          "Subject:{}\r\n\r\n"\
          "{}".format(SUPPORT_EMAIL, 
                      'SamplePro error in Config', 
                      'Failed to load {}. Default config.ini can be created with create_configini.py.\r\n\r\n{}'.format(get_config.config_filename(), err))
    s.sendmail('<donotreply@scionresearch.com>', [SUPPORT_EMAIL], msg)
    s.quit()
    #SUPPORT_EMAIL = 'wayne.schou@scionreesarch.com'  # need to specify email to use with config errors
    #email_Support('SamplePro error in Config', RuntimeError('Failed to load {}. Default config.ini can be created with create_configini.py'.format(get_config.config_filename())) )
    raise
API_URL = config['FreezerPro']['api_url']
USER_NAME = config['FreezerPro']['Username']
SMTPServer = config['MailServer']['SMTPServer']
SMTPPort = config['MailServer']['SMTPPort']
SEND_EMAIL_FROM = config['System'].get('send_email_from', fallback='SamplePro <donotreply@scionresearch.com>')
SUPPORT_EMAIL = config['System']['Support_Email']
OPERATION_OFFICER_EMAIL = config['System'].get('operation_officer_email', fallback='Operations.Officer@scionresearch.com')
VERITEC_EMAIL = config['System'].get('veritec_email', fallback='Veritec@scionresearch.com')
MEDIA_EMAIL = config['System'].get('media_email', fallback='TreePropagation@scionresearch.com')
EMAIL_SUPPORT_ONLY = config['System'].getboolean('EMAIL_SUPPORT_ONLY', fallback=False)
DAYS_TO_REVIEW_NORMAL = config['System'].getint('days_to_review_normal', fallback=30)
DAYS_TO_REVIEW_SHORT = config['System'].getint('days_to_review_short', fallback=7)

## Constants:
#API_URL = 'https://freezerpro.scionresearch.com/api'  # Production database
##API_URL = 'http://163.7.18.12/api' #Training database
#USER_NAME = 'Schouw'  #case-sensitive
#SMTPServer = '163.7.18.150'
#SMTPPort = 25
#SUPPORT_EMAIL = 'jenny.simpson@scionresearch.com' #'wayne.schou@scionresearch.com'  #

@unique
class Vial_States(IntEnum):
    """ Enumeration of Vial States ids (must match database table vial_state_types.id) """
    Received = 1
    WithOwner = 2
    Stored = 3
    StoreRequest = 4
    RetrieveRequest = 5
    ReturnToSource = 6,
    Returned = 7,
    DisposeRequest = 8
    Disposed = 9
    ApprovalRequested = 10,
    StoreRequestApproved = 11,
    AwaitingDelivery = 12,
    VeritecRequest = 13,
    SampleFinished = 14,
    SamplePartiallyUsed = 15,
    MediaRequest = 16,
    StoredSpare = 17,
    SendToExternal = 18,
    SampleUnused = 19,
    SampleDestroyed = 20

STATE_NAME = {
    Vial_States.Received:'Stores - Received',
    Vial_States.WithOwner:'With Owner/In Lab',
    Vial_States.Stored:'Stored',
    Vial_States.StoreRequest:'Stores - Request to Store',
    Vial_States.RetrieveRequest:'Stores - Request to Retrieve',
    Vial_States.ReturnToSource:'Stores - Return to Source',
    Vial_States.Returned:'Returned',
    Vial_States.DisposeRequest:'Stores - Request to Dispose',
    Vial_States.Disposed:'Disposed',
    Vial_States.ApprovalRequested:'Lead - Request to Extend Storage',
    Vial_States.StoreRequestApproved:'Lead - Request to Extend Storage Approved',
    Vial_States.AwaitingDelivery:'Awaiting Delivery',
    Vial_States.VeritecRequest:'Veritec Request',
    Vial_States.SampleFinished: 'Sample - Finished, Live Derivs',
    Vial_States.SamplePartiallyUsed: 'Sample - Partially Used',
    Vial_States.MediaRequest:'Media Request',
    Vial_States.StoredSpare:'Stored - Spare',
    Vial_States.SendToExternal:'Stores - Send to External',
    Vial_States.SampleUnused:'Sample - Unused',
    Vial_States.SampleDestroyed:'Sample - Destroyed'
    }

auth_token = None


def get_token():
    """ Get Authorization token
    """
    password = keyring.get_password('FreezerPro', USER_NAME)
    if not password:
        raise RuntimeError('Password for {} has not been stored. Use set_password.py.'.format(USER_NAME))
    urllib3.disable_warnings(category=InsecureRequestWarning)
    r = requests.post(API_URL,
                      data={'method': 'gen_token' },
                      auth=(USER_NAME, password), verify=False)
    r.raise_for_status()
    data = r.json()
    # print(json.dumps(data, indent=4, sort_keys=True))
    if 'auth_token' in data:
        auth_token = data['auth_token']
        return auth_token
    elif 'error' in data:
        raise RuntimeError('{}'.format(data['message']))
    else:
        raise RuntimeError('Unexpected result returned: {}'.format(data))


def freezerpro_post(params, file={}):
    """ 
    Wrapper for posting to FreezerPro api using authorization token
    Token will be requested if needed
    :param params: dictionary of parameters
    :return: dictionary of results
    """
    global auth_token
    if not auth_token:
        auth_token = get_token()
    params['username'] = USER_NAME
    params['auth_token'] = auth_token
    urllib3.disable_warnings(category=InsecureRequestWarning)
    r = requests.post(API_URL, 
                      headers={'Content-Type': 'application/json'},
                      # data=json.dumps(params), 
                      json=params,
                      files=file,
                      verify=False )
    r.raise_for_status()
    data = r.json()
    if 'error' in data:
        if 'message' in data:
            raise RuntimeError('{}'.format(data['message']))
        else:
            raise RuntimeError('Unexpected result returned: {}'.format(data))
    return data


def freezerpro_retrieve(params, resultName):
    """ 
    Wrapper for retrieving data from freezerpro where results could exceed hard limit of 1000 values
    Need to use limit and start parameters to make multiple calls
    :param params: dictionary of parameters
    :param resultName: key value that is returned from call (typically Total and one other key)
    :return: list of results
    """
    params['limit'] = 1000
    data = freezerpro_post(params)
    results = data[resultName]
    total = data['Total']
    while len(results) < total:
        params['start'] = len(results)
        params['dir'] = 'ASC'
        more = freezerpro_post(params)
        if (len(more[resultName]) == 0):
            print('freezerpro_retrieve: All results not returned Total={} Returned={}'.format(total, len(results)))
            break
        results.extend(more[resultName])
    return results    


def get_users():
    data = freezerpro_post({'method': 'users'})
    users = data['Users']
    if data['Total'] != len(users):
        raise RuntimeError('get_users: not all users retrieved')
    return users


def get_sample(sample_id):
    """
    'name':
    'description':
    'icon':
    'sample_type':
    'source':
    'source_id':
    'group_ids':
    'scount':
    'volume':
    'vol_freezers':
    'owner':
    'expiration':
    'created_at':
    'updated_at':
    'location':
    """
    sample = freezerpro_post({'method': 'sample_info',
                            'id': sample_id,
                           })
    return sample


def get_sample_userfields(sample_id):
    udfs = freezerpro_post({'method': 'sample_userfields',
                            'id': sample_id})
    return udfs


def get_location(location_id):
    location = freezerpro_post({'method': 'location_info',
                            'id': location_id,
                           })
    return location


def get_vials(sample_id):
    data = freezerpro_post({'method': 'vials_sample',
                            'sample_id': sample_id,
                           })
    vials = data['Locations']
    if data['Total'] != len(vials):
        raise RuntimeError('get_vials: Not all vials retrieved')
    return vials


def get_audit(date_flag):
    data = freezerpro_post({'method': 'audit',
                            'date_flag': date_flag,
                            'dir': 'ASC',
                            'limit': 1000,  #1000 is maximum that can be returned
                            })
    audits = data['AuditRec']
    total = data['Total']
    while len(audits) < total:
        more = freezerpro_post({'method': 'audit',
                            'date_flag': date_flag,
                            'limit': 1000,  #1000 is maximum that can be returned
                            'start': len(audits),
                            'dir': 'ASC',
                            })
        if (len(more['AuditRec']) == 0):
            print('get_audit: All audits not returned Total={} Returned={}'.format(total, len(audits)))
            break
        audits.extend(more['AuditRec'])
    return audits


def get_locations_in_state(state, sdfs=[]):
    """
    Get all locations with given state
    :param state: vial_state_type_id
    :param sdfs: optional list of udfs that will be appended to locations (set to None if not present)
    :return: list of locations
    """
    data = freezerpro_post({'method': 'vials_sample',
                            'vial_state_type_id': state,
                            'dir': 'ASC',
                            'limit':1000,
                           })
    # print(json.dumps(data, indent=4, sort_keys=True))
    locations = data['Locations']
    total = data['Total']
    while len(locations) < total:
        more = freezerpro_post({'method': 'vials_sample',
                                'vial_state_type_id': state,
                                'limit':1000,
                                'start':len(locations),
                                'dir': 'ASC'})
        if len(more['Locations']) == 0:
            print('get_audit: All locations not returned Total={} Returned={}'.format(total, len(locations)))
            break
        locations.extend(more['Locations'])
    # print('Locations =', data['Total'])    
    if sdfs:
        for location in locations:
            udfs = freezerpro_post({'method': 'sample_userfields',
                                    'id': location['sample_id']})
            for udf in sdfs:
                if udf in udfs:
                    location[udf] = udfs[udf]
                else:
                    location[udf] = None    
    return locations


def get_group_userids(group_name):
    """
    Get user ids of users associated with given group
    :param group_name: name of a existing FreezerPro user_group
    :return: list of user_ids
    """
    data = freezerpro_post({'method': 'user_groups'})
    groups = data['Groups']
    # print('Groups: ', [group['name'] for group in groups])
    # print()
    group = next((group for group in groups if group['name'] == group_name), None)
    if not group:
        raise RuntimeError('No such user_group {}'.format(group_name))
    users = group['users']
    ids = [group_user['id'] for group_user in users]
    return ids


def get_users_by_group(group_name):
    userids = get_group_userids(group_name)
    users = get_users_by_id(userids)
    return users


def get_users_by_fullname(usernames):
    allusers = get_users()
    users = [next((u for u in allusers if u['fullname'] == user_name), None) for user_name in usernames]
    return users


def get_users_by_username(usernames):
    allusers = get_users()
    users = [next((u for u in allusers if u['username'] == user_name), None) for user_name in usernames]
    return users


def get_users_by_id(userids):
    allusers = get_users()
    users = [next((u for u in allusers if u['id'] == userid), None) for userid in userids]
    return users


def dict_to_html(data, keys, headers):
    """ Create html table from list of dictionaries
    :param data: list of dictionaries
    :param keys: list of dictionary keys to use in presentation order
    :param header: list of strings to use for column headers (must match keys)
    return: html text for populated table
    """
    pd.set_option('display.max_colwidth',999)
    df = pd.DataFrame(data)[keys]
    df.columns = headers
    html = df.to_html(escape=False, index=False)
    return html


def send_html(to, email_addresses, subject, msg):
    s = smtplib.SMTP(SMTPServer, SMTPPort)

    message = MIMEText(msg, 'html', 'utf-8')

    message['From'] = SEND_EMAIL_FROM
    message['To'] = to
    message['Subject'] = subject

    msg_full = message.as_string()
    if EMAIL_SUPPORT_ONLY:
        email_addresses = [SUPPORT_EMAIL]
    s.sendmail('donotreply@scionresearch.com', email_addresses, msg_full)
    s.quit()


def send(to, email_addresses, subject, msg):
    s = smtplib.SMTP(SMTPServer, SMTPPort)

    if isinstance(msg, Exception):
        msg = str(msg) +'\n\n' + ''.join(traceback.format_exception(type(msg), msg, msg.__traceback__))
    msg = "From: {}\r\n"\
          "To: {}\r\n"\
          "Subject:{}\r\n\r\n"\
          "{}".format(SEND_EMAIL_FROM, to, subject, msg)
    if EMAIL_SUPPORT_ONLY:
        email_addresses = [SUPPORT_EMAIL]
    s.sendmail('<donotreply@scionresearch.com>', email_addresses, msg)
    s.quit()


def email_group(group_to_email, subject, msg):
    users = get_users_by_group(group_to_email)
    emails = [user['email'] for user in users]
    emails = list(filter(None, emails))
    if not emails:
        raise RuntimeError('No users with emails in group {}'.format(group_to_email))

    send_html(group_to_email, emails, subject, msg)


def email_OperationsOfficer(subject, msg):
    # email_group('Operations Officer', subject, msg)
    send_html('Operation Officer', [OPERATION_OFFICER_EMAIL], subject, msg)


def email_Veritec(subject, msg):
    send_html('Veritec', [VERITEC_EMAIL], subject, msg)


def email_MediaRequests(subject, msg):
    send_html('Tree Propagation', [MEDIA_EMAIL], subject, msg)


def email_Support(subject, msg):
    send('SamplePro Support', [SUPPORT_EMAIL], subject, msg )


def samples_with_state_changes(date_flag, states=None):
    """ Return list of samples that have one of the specified state changes in the period specified
    :date_flag: all/today/yesterday/week/month/'date_from,date_to'
    :states: iterable of state strings to check 
     ("Store Request", "Retrieve Request", "Dispose Request", "Approval Requested", "Stored", 
      "Retrieved", "With Owner", "Disposed", "Return to Source", "Store Request Approved", "Awaiting Delivery")
    """
    audits = get_audit(date_flag)
    #for audit in audits:
    #    print(audit)
    #obj_names = set([audit['obj_name'] for audit in audits])
    #print(obj_names)
    # states = ['Store Request', 'Retrieve Request', 'Dispose Request']
    # mm = [audit for audit in audits if audit['obj_name'] in states]
    if not states:
        states = STATE_NAME.values()
    state_changes = [{'type': audit['obj_name'], 
                        'date': audit['created_at'],
                        'user_name': audit['user_name'],
                        'message': audit['message'],  
                        'comments': audit['comments']} 
                        for audit in audits if audit['obj_name'] in states]
    #extract sample_id from message and add as distinct key
    for m in state_changes:
        pattern = 'State for vial <u>"(.*?)"<\/u>(?:.*?) ID: <u>(\d+)<\/u> changed from "(.*?)" to "(.*?)"'
        # pattern = 'State for vial <u>"(.*?)"<\/u>(?:.*?) ID: <u>(\d+)<\/u>(?:.*)'
        match = re.match(pattern, m['message'])
        m['vial_location'] = match.groups()[0]
        m['sample_id'] = match.groups()[1]
        m['from_state'] = match.groups()[2]
        m['to_state'] = match.groups()[3]
        # print(m['date'], m['type'], 'for sample', m['sample_id'], 'by', m['user_name'])
    return state_changes


def samples_nearing_reviewdate(days):
    """Will exclude samples that have been disposed, disposerequest, returned or returntosource
    """
    today = date.today()
    before_date = today + timedelta(days=days+1)
    after_date = today - timedelta(days=1)
    data = freezerpro_post({'method': 'advanced_search',
                            'query': [{'type': 'udf',
                                       'field': 'Review Date',
                                       'op': 'gt',
                                       'value': after_date.strftime('%d/%m/%Y')
                                      },
                                      {'type': 'udf',
                                       'field': 'Review Date',
                                       'op': 'lt',
                                       'value': before_date.strftime('%d/%m/%Y')
                                      },
                                     ],
                            'sdfs': ['id', 'sample_type', 'owner_id', 'created_at'],
                            'udfs': ['Review Date'],
                            })
    samples = data['Samples']
    if data['Total'] != len(samples):
        raise RuntimeError('Not all returned')
    for sample in samples[:]:
        sample['Review Date'] = sample['udfs']['Review Date']
        sample_rec = get_sample(sample['id'])
        sample['location'] = sample_rec['location']  # add location result
        # exclude samples where all vials in state DisposeRequested, Disposed, Returned, or ReturnToSource
        vials = get_vials(sample['id'])
        b_all_gone = True
        for vial in vials:
            if vial['state_info'] not in [STATE_NAME[Vial_States.Disposed], 
                                      STATE_NAME[Vial_States.DisposeRequest],
                                      STATE_NAME[Vial_States.Returned],
                                      STATE_NAME[Vial_States.ReturnToSource],
                                      STATE_NAME[Vial_States.SampleDestroyed]]:
                b_all_gone = False
                break
        if b_all_gone:
            samples.remove(sample)
    return samples


def samples_reviewdate_overdue():
    """Will exclude samples that have been disposed, disposerequest, returned or returntosource
    """
    today = date.today()
    data = freezerpro_post({'method': 'advanced_search',
                            'query': [{'type': 'udf',
                                       'field': 'Review Date',
                                       'op': 'lt',
                                       'value': today.strftime('%d/%m/%Y')
                                      },
                                     ],
                            'sdfs': ['id', 'sample_type', 'owner_id'],
                            'udfs': ['Review Date', 'Approval Contact'],
                            })
    samples = data['Samples']
    if data['Total'] != len(samples):
        raise RuntimeError('Not all returned')
    for sample in samples[:]:
        sample['Review Date'] = sample['udfs']['Review Date']
        sample['Approval Contact'] = sample['udfs']['Approval Contact']
        sample_rec = get_sample(sample['id'])
        sample['location'] = sample_rec['location']
        # exclude samples where all vials in state DisposeRequested, Disposed, Returned, or ReturnToSource
        vials = get_vials(sample['id'])
        b_all_gone = True
        for vial in vials:
            if vial['state_info'] not in [STATE_NAME[Vial_States.Disposed], 
                                      STATE_NAME[Vial_States.DisposeRequest],
                                      STATE_NAME[Vial_States.Returned],
                                      STATE_NAME[Vial_States.ReturnToSource],
                                      STATE_NAME[Vial_States.SampleDestroyed]]:
                b_all_gone = False
                break
        if b_all_gone:
            samples.remove(sample)
    return samples


def create_html_msg_about_states(*states):
    """
    Create msg ready for email whenever locations are in any of the states specified
    :param *states: iterable of Vial_States
    :return: html msg else None if no samples in specified states
    """
    sampleids_by_currentstate = {"'"+state+"'":set() for state in STATE_NAME.values()}
    msg = []
    bSend_email = False
    for state in states:
        locations = get_locations_in_state(state.value)
        if not locations:
            msg.append('No samples have status <b>{}</b>.'.format(STATE_NAME[state]))
            msg.append('')
            continue
        bSend_email = True
        for location in locations:
            sample = get_sample(location['sample_id'])
            location['owner'] = sample['owner']
            sampleids_by_currentstate["'"+STATE_NAME[state]+"'"].add(str(location['sample_id']))
        # print('Location fields', locations[0].keys())
        msg.append('These samples currently have status <b>{}</b>:'.format(STATE_NAME[state]))
        html = dict_to_html(locations, 
                            ['sample_id', 'barcode_tag', 'sampletype_name', 'location', 'position', 'owner'], 
                            ['Sample Id', 'Barcode', 'Sample Type', 'Location', 'Position', 'Owner'])
        msg.append(html)
        msg.append('')

    if not bSend_email:  # no samples in states
        return None

    # retreive names for selected vial state id
    vial_state_names = ["'"+STATE_NAME[state_id]+"'" for state_id in states]

    sample_state_changes = samples_with_state_changes('today')
    # remove state changes not in states
    for state_change in sample_state_changes[:]:
        if state_change['to_state'] not in vial_state_names: 
            sample_state_changes.remove(state_change)
        elif state_change['sample_id'] not in sampleids_by_currentstate[state_change['to_state']]:
            print("Remove sample not currently in state", state_change)
            sample_state_changes.remove(state_change)
        else:
            # print(state_change['date'], state_change['type'], 'for sample', state_change['sample_id'], 'by', state_change['user_name'])
            sample = get_sample(state_change['sample_id'])
            #state_change['sample_name'] = sample['name']
            state_change['owner'] = sample['owner']
            state_change['sample_type'] = sample['sample_type']

    if sample_state_changes:
        msg.append('Further details about samples changed today: {:%d/%m/%Y}'.format(datetime.now()))
        html = dict_to_html(sample_state_changes, 
                            ['sample_id', 'sample_type', 'owner', 'from_state', 'to_state', 'user_name', 'vial_location', 'comments'],  
                            ['Sample Id', 'Sample Type', 'Owner', 'From State', 'To State', 'Changed by', 'Location', 'Comments'])
        msg.append(html)
        msg.append('')

    sample_state_changes = samples_with_state_changes('yesterday')
    # remove state changes not in states
    for state_change in sample_state_changes[:]:
        if state_change['to_state'] not in vial_state_names: 
            sample_state_changes.remove(state_change)
        elif state_change['sample_id'] not in sampleids_by_currentstate[state_change['to_state']]:
            print("Remove sample not currently in state", state_change)
            sample_state_changes.remove(state_change)
        else:
            # print(state_change['date'], state_change['type'], 'for sample', state_change['sample_id'], 'by', state_change['user_name'])
            sample = get_sample(state_change['sample_id'])
            #state_change['sample_name'] = sample['name']
            state_change['owner'] = sample['owner']
            state_change['sample_type'] = sample['sample_type']

    if sample_state_changes:
        msg.append('Further details about samples changed yesterday: {:%d/%m/%Y}'.format(datetime.now() - timedelta(days=1)))
        html = dict_to_html(sample_state_changes, 
                            ['sample_id', 'sample_type', 'owner', 'from_state', 'to_state', 'user_name', 'vial_location', 'comments'],  
                            ['Sample Id', 'Sample Type', 'Owner', 'From State', 'To State', 'Changed by', 'Location', 'Comments'])
        msg.append(html)
        msg.append('')

    # email_OperationsOfficer('SamplePro requests', '<br>\r\n'.join(msg))

    return '<br>\r\n'.join(msg)
