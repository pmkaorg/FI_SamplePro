#! python3
""" Email owners of samples any samples where Review Date has passed
Will not report on samples where ANY sample vial/location has a Disposed or Dispose Request state
"""

from FreezerPro import samples_reviewdate_overdue, dict_to_html, send_html, email_Support, get_users_by_id, SUPPORT_EMAIL

def email_owners_reviewdate_overdue():
    samples = samples_reviewdate_overdue()
    # print(samples)
    sample_owner_ids = set([sample['owner_id'] for sample in samples])
    sample_owners = get_users_by_id(sample_owner_ids)
    # print(sample_owners)
    for user in sample_owners:
        samples_of_owner = [sample for sample in samples if sample['owner_id'] == user['id']]
        # print('Samples of owner', samples_of_owner)
        msg = ['The following samples owned by you have an overdue review date']
        samples.sort(key=lambda x: x['Review Date'] + x['location'] + str(x['id']).zfill(10))
        html = dict_to_html(samples_of_owner, 
                            ['id', 'Review Date', 'location'], 
                            ['Sample Id', 'Review Date', 'Location'])
        msg.append(html)

        #print(user['fullname'], '[', user['email'], ']')
        #print('\n'.join(msg))

        send_html(user['fullname'], [user['email']], 'SamplePro: Overdue Review dates', '<br>\r\n'.join(msg))
    return sample_owners


if __name__ == '__main__':
    try:
        email_sent = email_owners_reviewdate_overdue()
        print('Email sent', email_sent)
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in EmailOwnersSampleReviewDateOverdue', err )