#! python3
""" Email user in "Approval Contact" udf of sample about samples with ApprovalRequested status
Any samples with an invalid "Approval Contact" (in state ApprovalRequested) will be sent to OperationsOfficer group
Author: Wayne Schou
Date: August 2018

"""

from FreezerPro import send_html, dict_to_html, email_OperationsOfficer, email_Support, Vial_States, STATE_NAME,\
    get_locations_in_state, get_users_by_fullname, get_sample, SUPPORT_EMAIL


def email_sample_udf_about_state_change(user_udf, state):
    """
    Email user stored in user_udf field of sample about sample in specified state
    :param user_udf: name of udf field holding username e.g 'Approval Contact'
    :param states: Vial_States
    :return: True if email sent else False if no locations in specified states
    """
    locations = get_locations_in_state(state.value, [user_udf])
    if not locations:
        return None
    for location in locations:
        sample = get_sample(location['sample_id'])
        location['owner'] = sample['owner']
        location['sample_type'] = sample['sample_type']

    udf_usernames = set([location[user_udf] for location in locations])
    users = get_users_by_fullname(udf_usernames)  # will ignore locations without valid user_udf
    users = list(filter(None, users))
    valid_usernames = [user['fullname'] for user in users]
    invalid_udf_locations = [location for location in locations if location[user_udf] not in valid_usernames]
    if invalid_udf_locations:  # there are samples in specified state where user_udf does not contain valid user
        msg = []
        msg.append('These samples with status {} do not have a valid {}:'
                   .format(STATE_NAME[state], user_udf))
        html = dict_to_html(invalid_udf_locations, 
                            ['sample_id', 'barcode_tag', 'sample_type', 'owner', user_udf], 
                            ['Sample Id', 'Barcode', 'Sample Type', 'Owner', user_udf])
        msg.append(html)
        #msg.append('sample_id\tbarcode\t            Sample Type            \t     Owner     \t{:15}'.format(user_udf))
        #for location in invalid_udf_locations:
        #    msg.append('{:15}\t{:7}\t{:32}\t{:15}\t{}'
        #               .format(location['sample_id'], location['barcode_tag'], location['sample_type'], location['owner'], location[user_udf]))
        email_OperationsOfficer('Invalid {}'.format(user_udf), '<br>\r\n'.join(msg))
    for user in users:
        locations_of_user = [location for location in locations if location[user_udf] == user['fullname']]
        msg = []
        # print('Location fields', locations[0].keys())
        msg.append('These samples (with {}={}) currently have status {}:'
                   .format(user_udf, user['fullname'], STATE_NAME[state]))
        html = dict_to_html(locations_of_user, 
                            ['sample_id', 'barcode_tag', 'sample_type', 'owner'], 
                            ['Sample Id', 'Barcode', 'Sample Type', 'Owner'])
        msg.append(html)
        #msg.append('sample_id\tbarcode\t            Sample Type            \t     Owner')
        #for location in locations_of_user:
        #    msg.append('{:15}\t{:7}\t{:32}\t{}'.format(location['sample_id'], location['barcode_tag'], location['sample_type'], location['owner']))
        #msg.append('')

        send_html(user['fullname'], [user['email']], 'SamplePro: sample requests', '<br>\r\n'.join(msg))
    return users


if __name__ == '__main__':
    try:
        users_emailed = email_sample_udf_about_state_change('Approval Contact', Vial_States.ApprovalRequested)
        if users_emailed:
            emails = [user['email'] for user in users_emailed]
            print('Emails sent to ', emails)
        else:
            print('No samples have Approval Requested with Approval Contact set')
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in EmailApprovalContactAboutRequests', err )
