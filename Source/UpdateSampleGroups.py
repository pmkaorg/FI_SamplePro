#!/usr/bin/env python3
""" Update Sample Groups based on TechnologyOne Project and Task Codes

Author: Wayne Schou
Date: Dec 2018

"""

from FreezerPro import freezerpro_post


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


if __name__ == '__main__':
    data = freezerpro_retrieve({'method': 'sample_groups'}, 'SampleGroups')
    print(data)
    print(len(data))
    print(data[0])
