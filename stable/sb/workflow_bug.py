#!/usr/bin/env python
#
from logging                            import info, debug, error, warning, basicConfig, INFO, DEBUG, WARNING
import re

from ktl.termcolor                      import colored
from ktl.ubuntu                         import Ubuntu

def cinfo(msg, color='green'):
    info(colored(msg, color))

# WorkflowBugTask
#
class WorkflowBugTask(object):
    # __init__
    #
    def __init__(s, lp_task, task_name):
        setattr(s, 'name', task_name)
        setattr(s, 'status', lp_task.status)
        setattr(s, 'importance', lp_task.importance)
        setattr(s, 'lp_task', lp_task)

        assignee    = lp_task.assignee
        if assignee is None:
            setattr(s, 'assignee', '*Unassigned')
        else:
            setattr(s, 'assignee', assignee.display_name)

# WorkflowBug
#
class WorkflowBug():
    # __init__
    #
    def __init__(s, lp, projects, bugid, sauron=False):
        s.lp = lp
        s.lpbug = s.lp.get_bug(bugid)
        s.projects = projects
        s.sauron = sauron
        s.title = s.lpbug.title

        s.__package_name = None

        cinfo('                      title: "%s"' % s.title, 'blue')

        try:
            s.pkg_name = re.findall('linux[^:]*', s.title)[0]
        except IndexError:
            s.pkg_name = None
        cinfo('                   pkg_name: "%s"' % s.pkg_name, 'blue')

        try:
            s.pkg_version = re.findall('([0-9]+\.[^ ]+)', s.title)[0]
        except IndexError:
            s.pkg_version = None
        cinfo('                pkg_version: "%s"' % s.pkg_version, 'blue')

        if s.pkg_name is not None and s.pkg_version is not None:
            s.series = Ubuntu().series_name(s.pkg_name, s.pkg_version)
        else:
            s.series = None
        cinfo('                     series: "%s"' % s.series, 'blue')

        # If a bug isn't to be processed, detect this as early as possible.
        #
        s.is_valid = s.check_is_valid(s.lpbug)

        if s.is_valid:
            info('    Targeted Project:')
            info('        %s' % s.targeted_project)
            info('')
            s.properties = s.lpbug.properties
            if len(s.properties) > 0:
                info('    Properties:')
                for prop in s.properties:
                    info('        %s: %s' % (prop, s.properties[prop]))

            s.tasks_by_name = s.create_tasks_by_name()

    # check_is_valid
    #
    def check_is_valid(s, bug):
        '''
        Determine if this bug is one that we wan't to be processing.
        '''
        retval = True
        for t in s.lpbug.tasks:
            task_name       = t.bug_target_name

            if task_name in s.projects:
                s.targeted_project = task_name
                if t.status == 'In Progress':
                    continue
                else:
                    if s.sauron:
                        continue
                    info('        Not processing this bug because master task state is set to %s' % (t.status))
                    info('        Quitting this bug')
                    retval = False

        return retval

    # create_tasks_by_name
    #
    def create_tasks_by_name(s):
        '''
        We are only interested in the tasks that are specific to the workflow project. Others
        are ignored.
        '''
        tasks_by_name = {}

        info('')
        info('    Scanning bug tasks:')

        for t in s.lpbug.tasks:
            task_name       = t.bug_target_name

            if task_name.startswith(s.targeted_project):
                if '/' in task_name:
                    task_name = task_name[len(s.targeted_project)+1:].strip()
                tasks_by_name[task_name] = WorkflowBugTask(t, task_name)
            else:
                info('')
                info('        %-25s' % (task_name))
                info('            Action: Skipping non-workflow task')

        return tasks_by_name


