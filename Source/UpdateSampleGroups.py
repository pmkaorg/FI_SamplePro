#!/usr/bin/env python3
""" Update Sample Groups based on TechnologyOne Project and Task Codes
Sample groups that do not exist in SamplePro (by name) are added where name is
a combination of Science Group, Project Code, and Task Number e.g. BP 568 A49147 
Note: Sample groups are never removed from SamplePro and existing sample groups are not altered.
Note: Changes to task description do not cause an update in SamplePro

Input: csv file generated daily and saved to location as defined in config.ini [System | taskcode_file]
Output: Updated samples groups plus email to support if new sample groups added.
Config.ini:
    System | taskcode_file: path to csv of techone taskcodes e.g. C:\\SamplePro\\TaskCodes.csv
    System | taskcode_science_groups: list of science groups to import. e.g. ['FG', 'FS']. 

Exceptions (emailed to support):
    - Must define location of taskcode file in config.ini
    - {taskcode_file} not found
    - Must define taskcode_science_groups in config.ini e.g. taskcode_science_groups = ['FG', 'BP']

Author: Wayne Schou
Date: Mar 2019

"""

import csv
import time
import json
from FreezerPro import freezerpro_post, freezerpro_retrieve, email_Support
import get_config
from ast import literal_eval
from os.path import isfile


def import_samplegroups(task_codes):
    """ Import new sample groups

    Parameters:
        task_codes ([{Name, Description}]): list of new sample groups to add 

    Returns:
        job_id (str): job id of background job started (will have completed by time method returns)
    """

    import_response = freezerpro_post({'method': 'import_sample_groups', 'background_job': 'true', 'json':json.dumps(task_codes)})
    job_id = import_response['job_id']
    while(True):
        time.sleep(1)
        completed_response = freezerpro_post({'method':'get_job_status', 'job_id':job_id})
        if completed_response['status'] == 1:
            raise RuntimeError(completed_response['msg'] )
        if completed_response['status'] != 3:
            break
    return job_id


if __name__ == '__main__':
    try:
        existing_sample_groups = freezerpro_retrieve({'method': 'sample_groups'}, 'SampleGroups')

        # load TechOne tasks code list
        config = get_config.get_config()
        # taskcode_filename = config['System']['taskcode_file']
        taskcode_filename = config['System'].get('taskcode_file', fallback=None)
        assert taskcode_filename, 'Must define location of taskcode file in config.ini using taskcode_file attribute.'
        assert isfile(taskcode_filename), '{} not found'.format(taskcode_filename)
        try: 
            science_groups = literal_eval( config['System'].get('taskcode_science_groups', fallback='None' ))
        except Exception as err:
            raise ValueError("Error when reading config.ini taskcode_science_groups") from err
        assert science_groups, "Must define taskcode_science_groups in config.ini e.g. taskcode_science_groups = ['FG', 'BP']"
        taskcodes = []
        try:
            with open(taskcode_filename, 'r', newline='', encoding='utf-8-sig') as taskcode_file:
                dictreader = csv.DictReader(taskcode_file)
                for row in dictreader:
                    if (row['SELN_TYPE11_CODE'] in science_groups):
                        taskcodes.append({
                            'Name':'{} {} {}'.format(row['SELN_TYPE11_CODE'], row['Project_Code'], row['Task_Number']).strip(),
                            'Description': '{} - {}'.format(row['Project_Name'], row['Task_Description']).strip()})
        except Exception as err:
            raise Exception("Error when reading csv") from err
        # make taskcodes unique (by name)
        #identify new taskcodes
        existing_taskcodes = [sample_group['name'].strip() for sample_group in existing_sample_groups]
        new_taskcodes = [taskcode for taskcode in taskcodes if taskcode['Name'] not in existing_taskcodes]

        if new_taskcodes:
            import_samplegroups(new_taskcodes)
            msg = 'Added following {} sample groups in science groups {}\n{}'.format(len(new_taskcodes), science_groups, 
                                                                                     '   \n'.join([taskcode['Name'] + ' ' + taskcode['Description'] for taskcode in new_taskcodes]))
            email_Support('SamplePro Sample Group Updates', msg)
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in Update Sample Groups', err )
