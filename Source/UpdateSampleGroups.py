#!/usr/bin/env python3
""" Update Sample Groups based on TechnologyOne Project and Task Codes
Sample groups that do not exist in SamplePro (by name) are added where name is
a combination of Science Group, Project Code, and Task Number e.g. BP 568 A49147 
Note: Sample groups are never removed from SamplePro
Note: Changes to task description do not cause an update in SamplePro
Note: Only taks codes from science groups listed in SCIENCE_GROUPS list are processed (all others are ignored).

Input: csv file generated daily and saved to location as defined in config.ini [System | taskcode_file]


Author: Wayne Schou
Date: Dec 2018

"""

import csv
import time
import json
from FreezerPro import freezerpro_post, freezerpro_retrieve, email_Support
import get_config

""" Only use csv records belonging to these science groups (csv field SELN_TYPE11_CODE)
Note: BI is techone code for BT (both have been included in this list)
"""
SCIENCE_GROUPS = ['FG', 'FS', 'FP', 'BT', 'BI', 'CT', 'BP', 'WF']


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
        if completed_response['status'] != 3:
            break
    return job_id


if __name__ == '__main__':
    try:
        existing_sample_groups = freezerpro_retrieve({'method': 'sample_groups'}, 'SampleGroups')

        # load TechOne tasks code list
        config = get_config.get_config()
        taskcode_filename = config['System']['taskcode_file']
        taskcodes = []
        with open(taskcode_filename, 'r', newline='', encoding='utf-8-sig') as taskcode_file:
            dictreader = csv.DictReader(taskcode_file)
            for row in dictreader:
                if (row['SELN_TYPE11_CODE'] in SCIENCE_GROUPS):
                    taskcodes.append({
                        'Name':'{} {} {}'.format(row['SELN_TYPE11_CODE'], row['Project_Code'], row['Task_Number']),
                        'Description': '{} - {}'.format(row['Project_Name'], row['Task_Description'])})

        #identify new taskcodes
        existing_taskcodes = [sample_group['name'] for sample_group in existing_sample_groups]
        new_taskcodes = [taskcode for taskcode in taskcodes if taskcode['Name'] not in existing_taskcodes]

        if new_taskcodes:
            msg = 'Added following {} sample groups in science groups{}\n{}'.format(len(new_taskcodes), SCIENCE_GROUPS, '\n'.join(new_taskcodes))
            email_Support('SamplePro Sample Group Updates', msg)
            import_samplegroups(new_taskcodes)
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in Update Sample Groups', err )
