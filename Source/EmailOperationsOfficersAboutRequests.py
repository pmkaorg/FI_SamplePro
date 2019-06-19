#! python3
""" Email Operations Officer a list of sampleids and barcodes that have state
 Vial_States.RetrieveRequest, Vial_States.StoreRequest, Vial_States.DisposeRequest, Vial_States.ReturnToSource,
 Vial_States.SendToExternal, Vial_States.StoreRequestApproved, Vial_States.ApprovalRequested
Author: Wayne Schou
Date: Dec 2018

"""

from FreezerPro import create_html_msg_about_states, email_OperationsOfficer, email_Support, Vial_States


if __name__ == '__main__':
    try:
        msg = create_html_msg_about_states( 
                                Vial_States.RetrieveRequest, 
                                Vial_States.StoreRequest,
                                Vial_States.DisposeRequest,
                                Vial_States.ReturnToSource,
                                Vial_States.SendToExternal,
                                Vial_States.StoreRequestApproved,
                                Vial_States.ApprovalRequested)
        if msg:
            email_OperationsOfficer('SamplePro requests', msg)
            print('Email sent to operations officers')
        else:
            print('No samples in specified states')
    except Exception as err:
        # print(err)
        email_Support('SamplePro error in EmailOperationsOfficersAboutRequests', err )
