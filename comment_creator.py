#!/usr/local/bin/python3

import configparser

from api_objects import init_stepik, Comment
from redmine_utils import init_redmine, get_answered_issues_from_project, get_data_from_issue_to_answer_on_stepik, \
    set_issue_answered_on_stepik_status

SETTINGS_FILE_PATH = 'settings.properties'


def init():
    if not init_stepik(config['stepik']['api_host'], config['stepik']['client_id'],
                       config['stepik']['client_secret']):
        raise RuntimeError('Cannot connect to stepik instance')

    if not init_redmine(config['redmine']['api_host'], config['redmine']['api_key'], config['redmine']['project']):
        raise RuntimeError('Cannot connect to redmine server')


def answer_to_comment_on_stepik():
    comments = 0
    for issue in issues:
        comment_id, user_id, notes = get_data_from_issue_to_answer_on_stepik(issue)
        if notes:
            for note in notes:
                Comment.retrieve(int(comment_id)).reply_to(note)
            set_issue_answered_on_stepik_status(issue)
            comments += 1
    return comments


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(SETTINGS_FILE_PATH)
    init()
    issues = get_answered_issues_from_project()
    comments = answer_to_comment_on_stepik()
    print(Comment.retrieve(int(413604)))
    print(comments, 'comments were answered')
