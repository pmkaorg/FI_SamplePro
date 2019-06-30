#! python3
""" Update Sample UDF fields SampleState and SampleStateDate to match vial states
SampleState = Disposed if ALL vials Disposed
            = Returned if ALL vials ReturnedToSource or Disposed
            = Awaiting Delivery if ALL vials AwaitingDelivery, ReturnedToSource, or Disposed
            = Current if ANY vial not AwaitingDelivery, ReturnedToSource, or Disposed
"""

import json
import time
import datetime
from FreezerPro import samples_with_state_changes, get_sample, get_sample_userfields, get_vials, Vial_States, STATE_NAME,\
     freezerpro_post, email_Support, get_locations_in_state,freezerpro_retrieve, get_sampletypes


def update_samples(samples_to_update):
    """ Update Samples

    Parameters:
        samples_to_update ([{}]): list of dictionaries containing fields to update (plus UID)

    Returns:
        job_id (str): job id of background job started (will have completed by time method returns)
    """

    if not samples_to_update:
        return
    update_response = freezerpro_post({'method': 'update_samples', 'background_job': 'true', 'json':json.dumps(samples_to_update)})
    job_id = update_response['job_id']
    while(True):
        time.sleep(1)
        completed_response = freezerpro_post({'method':'get_job_status', 'job_id':job_id})
        if completed_response['status'] == 1:
            raise RuntimeError(completed_response['msg'])
        elif completed_response['status'] != 3:
            break
    return job_id


def find_samplestates(date_flag):
    """ Find samples that have SampleState not matching vial states.
    Search audits within defined date range for vial state changes.
    Set sample SampleState and SampleStateDate UDf fields where wrong.

    Parameters:
        date_flag (str): range of audits to check. Values include 'today', 'yesterday', 'week', 'month', 'all', 'dd/mm/yyy,dd/mm/yyyy' 

    Returns:
        ([{}], set): tuple of samples that need updating and a set of sample types that do not have SampleState udf (and state changed)
    """

    samples_to_update = {}
    sample_type_missing_udf = set()
    sample_state_changes = samples_with_state_changes(date_flag)
    for state_change in sample_state_changes[:]:
        sampleid = state_change['sample_id']
        udfs = get_sample_userfields(sampleid)
        current_state = udfs.get('SampleState', None)
        vials = get_vials(sampleid)
        if any(vial['state_info'] == STATE_NAME[Vial_States.AwaitingDelivery] for vial in vials):
            new_state = 'Awaiting Delivery'
        elif any(vial['state_info'] == STATE_NAME[Vial_States.Returned] for vial in vials):
            new_state = 'Returned'
        elif any(vial['state_info'] == STATE_NAME[Vial_States.Disposed] or \
                 vial['state_info'] == STATE_NAME[Vial_States.SampleDestroyed] or \
                 vial['state_info'] == STATE_NAME[Vial_States.SampleFinished] for vial in vials):
            new_state = 'Disposed'
        else:
            new_state = 'Current'

        if current_state != new_state:
            # print('Update state of sample {} from {} to {}'.format(sampleid, current_state, new_state))
            samples_to_update[sampleid] = {'UID':sampleid, 
                                           'SampleState': new_state, 
                                           'SampleStateDate': state_change['date']}
    return (list(samples_to_update.values()), sample_type_missing_udf)


def find_SampleStateByVialState(vial_state):
    """ Update SampleState for samples where some vial in specified vial_state
    Args:
        vial_state: Use this state to retrieve vials (
    State of samples to be updated may not match vial_state specified [e.g. sample has two vials (Disposed, Returned), 
      sample state will be set to Returned if vial_state Disposed or Returned is used.]
    Returns:
        list(dict): dict of sample ids, samplestate, samplestatedate (UID, SampleState, SampleStateDate) that shoudl be updated
    """
    samples_to_update = {}
    vials = get_locations_in_state(vial_state)
    for vial in vials:
        sampleid = state_change['sample_id']
        udfs = get_sample_userfields(sampleid)
        current_state = udfs.get('SampleState', None)
        sample_vials = get_vials(sampleid)
        new_state = None
        if any(vial['state_info'] == STATE_NAME[Vial_States.AwaitingDelivery] for vial in sample_vials):
            new_state = 'Awaiting Delivery'
        elif any(vial['state_info'] == STATE_NAME[Vial_States.Returned] for vial in sample_vials):
            new_state = 'Returned'
        elif any(vial['state_info'] == STATE_NAME[Vial_States.Disposed] or \
                 vial['state_info'] == STATE_NAME[Vial_States.SampleDestroyed] or \
                 vial['state_info'] == STATE_NAME[Vial_States.SampleFinished] for vial in sample_vials):
            new_state = 'Disposed'
        elif any(vial['state_info']):  # set to Current if some vial has non-empty state
            new_state = 'Current'        
        else:
            new_state = current_state  # don't change state if no vial has non-empty state
        if current_state != new_state:
            print('Update state of sample {} from {} to {}'.format(sampleid, current_state, new_state))
            samples_to_update[sampleid] = {'UID':sampleid, 
                                               'SampleState': new_state, 
                                               'SampleStateDate': datetime.datetime.now().date()}
    return list(samples_to_update.values())


def find_SampleStateBySampleType(sampletypes):
    """ Find SampleStates for samples with specified sample types that need updating
    Args:
        sampletypes: [list(str)] list of sample types names
    Returns:
        list(dict): dict of sample ids, samplestate, samplestatedate (UID, SampleState, SampleStateDate) that shoudl be updated
    """
    samples_to_update = {}
    samples = freezerpro_retrieve({'method': 'advanced_search',
                                   'query': [{'type': 'sdf',
                                              'field': 'sample_type_name',
                                              'op': 'eq',
                                              'value': sampletypes
                                              },
                                            ],
                                   'sdfs': ['id', 'sample_type_name'],
                                   'udfs': ['SampleState'],
                                  },
                                 'Samples')
    print('Found {} samples'.format(len(samples)))
    for sample in samples:
        current_state = sample['udfs'].get('SampleState', None)
        sample_vials = get_vials(sample['id'])
        #print(state_change['date'], state_change['type'], 'for sample', state_change['sample_id'], 'by', state_change['user_name'])
        #print(sample)
        #print(current_state)
        #print([vial['state_info'] for vial in vials])
        new_state = None
        if any(vial['state_info'] == STATE_NAME[Vial_States.AwaitingDelivery] for vial in sample_vials):
            new_state = 'Awaiting Delivery'
        elif any(vial['state_info'] == STATE_NAME[Vial_States.Returned] for vial in sample_vials):
            new_state = 'Returned'
        elif any(vial['state_info'] == STATE_NAME[Vial_States.Disposed] or \
                 vial['state_info'] == STATE_NAME[Vial_States.SampleDestroyed] or \
                 vial['state_info'] == STATE_NAME[Vial_States.SampleFinished] for vial in sample_vials):
            new_state = 'Disposed'
        elif any(vial['state_info'] for vial in sample_vials):  # set to Current if some vial has non-empty state
            new_state = 'Current'
        else:
            new_state = current_state  #'Current' # don't change samples where no vial state has been set
        if current_state != new_state:
            # print('Update state of sample {} from {} to {}'.format(sample['id'], current_state, new_state))
            samples_to_update[sample['id']] = {'UID':sample['id'], 
                                               'SampleState': new_state, 
                                               'SampleStateDate': datetime.datetime.now().date().strftime('%d/%m/%Y')}
    return list(samples_to_update.values())


def update_all_samples():
    """ Update samplestate of all samples where sampletype has field SampleState
    """
    bFailure = false
    sampletypes = get_sampletypes()
    sampletypes_with_samplestate = [sampletype['name'] for sampletype in sampletypes if 'SampleState' in sampletype['fieldlist']]
    for sampletype in sampletypes_with_samplestate:
        try:
            print(sampletype)
            samples_to_update = find_SampleStateBySampleType([sampletype])
            if samples_to_update:
                # print(samples_to_update)
                print(len(samples_to_update))
                update_samples(samples_to_update)
                print('Completed Update')
        except Exception as err:
            print('Failed to process', err)
            bFailure = true
    return bFailure


if __name__ == '__main__':
    try:
        #(samples_to_update, sample_type_missing_udf) = find_samplestates('all')
        #(samples_to_update, sample_type_missing_udf) = set_SampleState(Vial_States.SampleFinished)
        #(samples_to_update, sample_type_missing_udf) = set_SampleState(Vial_States.Disposed)
        #(samples_to_update, sample_type_missing_udf) = set_SampleState(Vial_States.Returned)
        #(samples_to_update, sample_type_missing_udf) = set_SampleState(Vial_States.AwaitingDelivery)
        (samples_to_update, sample_type_missing_udf) = find_samplestates('yesterday')
        if samples_to_update:
            # print(samples_to_update)
            print(len(samples_to_update))
            update_samples(samples_to_update)
            print('Completed Update')
        if sample_type_missing_udf:
            email_Support('SamplePro Sample Types missing SampleState and SampleStateDate UDF', 
                          'The following sample types do not have user-defined fields "SampleState" and "SampleStateDate"\n'+
                          '\n'.join(sample_type_missing_udf))
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in UpdateSampleStateUDF', err )