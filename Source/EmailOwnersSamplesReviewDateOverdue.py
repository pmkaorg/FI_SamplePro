#! python3
""" Email owners of samples and approval contacts of any samples where Review Date has passed
Will not report on samples where ANY sample vial/location has a Disposed, Dispose Request, Returned, ReturnToSource or SampleDestroyed state
"""

from FreezerPro import samples_reviewdate_overdue, dict_to_html, send_html, email_Support, \
    get_users_by_id, get_users_by_fullname, SUPPORT_EMAIL


def email_owners_reviewdate_overdue(samples):
    # print(samples)
    sample_owner_ids = set([sample['owner_id'] for sample in samples])
    sample_owners = get_users_by_id(sample_owner_ids)
    # print(sample_owners)
    for user in sample_owners:
        samples_of_owner = [sample for sample in samples if sample['owner_id'] == user['id']]
        # print('Samples of owner', samples_of_owner)
        msg = ['The following samples owned by you have an overdue review date:']
        html = dict_to_html(samples_of_owner, 
                            ['id', 'Review Date', 'location'], 
                            ['Sample Id', 'Review Date', 'Location'])
        msg.append(html)
        #print(user['fullname'], '[', user['email'], ']')
        #print('\n'.join(msg))
        send_html(user['fullname'], [user['email']], 'SamplePro: Overdue Review dates', '<br>\r\n'.join(msg))

    return sample_owners


def email_approvalcontacts_reviewdate_overdue(samples):
    approvalcontacts = set([sample['Approval Contact'] for sample in samples])
    approval_users = get_users_by_fullname(approvalcontacts)  # will ignore locations without valid approval contact
    approval_users = list(filter(None, approval_users))  # remove empty entries (invalid) from list
    print(approval_users)
    for user in approval_users:
        print(user['email'])
        samples_of_approval = [sample for sample in samples if sample['Approval Contact'] == user['fullname']]
        # print('Samples of owner', samples_of_owner)
        msg = ['The following samples, where you are the Approval Contact, have an overdue review date:']
        html = dict_to_html(samples_of_approval, 
                            ['id', 'Review Date', 'location'], 
                            ['Sample Id', 'Review Date', 'Location'])
        msg.append(html)
        send_html(user['fullname'], [user['email']], 'SamplePro: Overdue Review dates', '<br>\r\n'.join(msg))
    return approval_users


def email_reviewdate_overdue():
    try:
        samples = samples_reviewdate_overdue()
        if samples:
            samples.sort(key=lambda sample: sample['Review Date'] + sample['location'] + str(sample['id']).zfill(10))
            # email owners when overdue
            owners = email_owners_reviewdate_overdue(samples)
            print('Email sent to owners', owners)
            # also email approval contacts
            approvers = email_approvalcontacts_reviewdate_overdue(samples)
            print('Email sent to approval contacts', approvers)
        else:
            print('No samples are overdue')
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in EmailOwnersSampleReviewDateOverdue', err )


if __name__ == '__main__':
    email_reviewdate_overdue()
