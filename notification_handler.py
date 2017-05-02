#!/usr/local/bin/python3

import configparser

from api_objects import init_stepik, Notification, Comment
from redmine_utils import sync_comment_chain, init_redmine

config = configparser.ConfigParser()
config.read('settings.properties')

if not init_stepik(config['stepik']['api_host'], config['stepik']['client_id'],
                   config['stepik']['client_secret']):
    raise RuntimeError('Cannot connect to stepik instance')

if not init_redmine(config['redmine']['api_host'], config['redmine']['api_key'], config['redmine']['project']):
    raise RuntimeError('Cannot connect to redmine server')


handled = 0
for notification in Notification.auto_paging_iter(is_unread=True, type='comments'):
    comment = Comment.get_chain(notification)

    if sync_comment_chain(comment):
        handled += int(notification.make_read())

print(handled, 'notifications were handled')

