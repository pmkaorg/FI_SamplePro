#!/usr/bin/env python3
""" Email Veritec a list of sampleids and barcodes that have state 'Veritec Request'

Author: Wayne Schou
Date: Dec 2018

"""

from FreezerPro import create_html_msg_about_states, email_Veritec, email_Support, Vial_States

if __name__ == '__main__':
    try:
        msg = create_html_msg_about_states(Vial_States.VeritecRequest)
        if msg:
            email_Veritec('SamplePro requests', msg)
            print('Email sent to Veritec')
        else:
            print('No samples in specified states')
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in EmailVeritecAboutRequests', err )
