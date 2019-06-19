#!/usr/bin/env python3
""" Email a list of sampleids and barcodes that have state 'Media Request'

Author: Wayne Schou
Date: Dec 2018

"""

from FreezerPro import create_html_msg_about_states, email_MediaRequests, email_Support, Vial_States

if __name__ == '__main__':
    try:
        msg = create_html_msg_about_states(Vial_States.MediaRequest)
        if msg:
            email_MediaRequests('SamplePro requests', msg)
            print('Email sent about MediaRequests')
        else:
            print('No samples in specified states')
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in EmailAboutMediaRequests', err )
