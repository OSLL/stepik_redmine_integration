#!/usr/local/bin/python3

import configparser

from api_objects import init_stepik, Comment

config = configparser.ConfigParser()
config.read('settings.properties')

if not init_stepik(config['stepik']['api_host'], config['stepik']['client_id'],
                   config['stepik']['client_secret']):
    raise RuntimeError('Cannot connect to stepik instance')

Comment.retrieve(386337).reply_to('Да, вы молодец')
