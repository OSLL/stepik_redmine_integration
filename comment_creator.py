#!/usr/local/bin/python3

import configparser

from api_objects import init_stepik, Comment

SETTINGS_FILE_PATH = '/home/jenkins/settings.properties'

config = configparser.ConfigParser()
config.read(SETTINGS_FILE_PATH)

if not init_stepik(config['stepik']['api_host'], config['stepik']['client_id'],
                   config['stepik']['client_secret']):
    raise RuntimeError('Cannot connect to stepik instance')

Comment.retrieve(386337).reply_to('Да, вы молодец')
