#! python3
""" Email owners of samples when samples are within 30 days of Review Date
Will not report on samples where ANY sample vial/location has a Disposed or Dispose Request state
"""

from FreezerPro import samples_nearing_reviewdate, dict_to_html, send_html, email_Support, get_users_by_id, SUPPORT_EMAIL, \
                       DAYS_TO_REVIEW_NORMAL, DAYS_TO_REVIEW_SHORT
from datetime import datetime

# number of days between creation and review date where sample is considered short term
SHORT_TERM_SAMPLE = 42

def email_owners_longterm_samples_nearing_reviewdate(days):
    samples = samples_nearing_reviewdate(days)
    samples = [sample for sample in samples 
               if (datetime.strptime( sample['Review Date'], '%d/%m/%Y') - datetime.strptime(sample['created_at'], '%d/%m/%Y')).days 
                   > SHORT_TERM_SAMPLE
              ]
    # print(samples)
    # users = get_users()
    sample_owner_ids = set([sample['owner_id'] for sample in samples])
    sample_owners = get_users_by_id(sample_owner_ids)
    # print(sample_owners)
    for user in sample_owners:
        samples_of_owner = [sample for sample in samples if sample['owner_id'] == user['id']]
        # print('Samples of owner', samples_of_owner)
        msg = ['The following samples owned by you require review within the next <b>{}</b> days'.format(days)]
        samples.sort(key=lambda x: x['Review Date'] + x['location'] + str(x['id']).zfill(10))
        html = dict_to_html(samples_of_owner, 
                            ['id', 'Review Date', 'location'], 
                            ['Sample Id', 'Review Date', 'Location'])
        msg.append(html)

        #print(user['fullname'], '[', user['email'], ']')
        #print('\n'.join(msg))

        send_html(user['fullname'], [user['email']], 'SamplePro: Review dates near', '<br>\r\n'.join(msg))
    return sample_owners


def email_owners_shortterm_samples_nearing_reviewdate(days):
    samples = samples_nearing_reviewdate(days)
    samples = [sample for sample in samples 
               if (datetime.strptime( sample['Review Date'], '%d/%m/%Y') - datetime.strptime(sample['created_at'], '%d/%m/%Y')).days 
                    <= SHORT_TERM_SAMPLE
              ]
    # print(samples)
    # users = get_users()
    sample_owner_ids = set([sample['owner_id'] for sample in samples])
    sample_owners = get_users_by_id(sample_owner_ids)
    # print(sample_owners)
    for user in sample_owners:
        samples_of_owner = [sample for sample in samples if sample['owner_id'] == user['id']]
        # print('Samples of owner', samples_of_owner)
        msg = ['The following samples owned by you require review within the next <b>{}</b> days'.format(days)]
        samples.sort(key=lambda x: x['Review Date'] + x['location'] + str(x['id']).zfill(10))
        html = dict_to_html(samples_of_owner, 
                            ['id', 'Review Date', 'location'], 
                            ['Sample Id', 'Review Date', 'Location'])
        msg.append(html)

        #print(user['fullname'], '[', user['email'], ']')
        #print('\n'.join(msg))

        send_html(user['fullname'], [user['email']], 'SamplePro: Review dates near', '<br>\r\n'.join(msg))
    return sample_owners


if __name__ == '__main__':
    try:
        email_sent = email_owners_longterm_samples_nearing_reviewdate(DAYS_TO_REVIEW_NORMAL)
        print('Normal term sample emails sent to', email_sent)
        email_sent = email_owners_shortterm_samples_nearing_reviewdate(DAYS_TO_REVIEW_SHORT)
        print('Short term sample emails sent to', email_sent)    
    except Exception as err:
        print(err)
        email_Support('SamplePro error in EmailOwnersSampleNearingReviewDate', err )
