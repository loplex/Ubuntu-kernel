#!/usr/bin/env python
#

from logging                            import info, debug, error, warning, basicConfig, INFO, DEBUG, WARNING

class PromoteToRelease():
    # __init__
    #
    def __init__(s, targeted_project, task):
        s.task = task

    # action
    #
    def action(s):
        info('        PromoteToRelease.action: %s' % s.task.name)

# vi:set ts=4 sw=4 expandtab syntax=python:
