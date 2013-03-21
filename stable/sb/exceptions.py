#!/usr/bin/env python
#

# GeneralError
#
class GeneralError(Exception):
    '''
    Generic base class for my exceptions.
    '''
    def __init__(s, emsg):
        s.__message = emsg

    @property
    def message(s):
        '''
        The shell command that was being executed when the timeout occured.
        '''
        return s.__message

# ErrorExit
#
class ErrorExit(GeneralError):
    '''
    If an error message has already been displayed and we want to just exit the app, this
    exception is raised.
    '''
    def __init__(s, emsg):
        GeneralError(emsg)

