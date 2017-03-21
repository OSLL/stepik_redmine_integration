import configparser

import requests

from stepik_utils import get_comment, get_comment_ids

config = configparser.ConfigParser()
config.read('settings.properties')

client_id = config['stepik']['client_id']
client_secret = config['stepik']['client_secret']
stepik_api_host = config['stepik']['api_host']

link = 'https://stepik.org/lesson/%D0%A1%D0%B5%D0%BC%D0%B8%D0%BD%D0%B0%D1%80-5-%D0%9A%D1%80%D0%B8%D1%82%D0%B5%D1%80%D0%B8%D0%B8-%D1%81%D0%BE%D0%B3%D0%BB%D0%B0%D1%81%D0%B8%D1%8F-42256/step/2?discussion=356722&reply=356960'


auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepik.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth)
token = resp.json().get('access_token')
if not token:
    raise RuntimeWarning('Client id/secret is probably incorrect')

root_id, comment_id = get_comment_ids(link)

root_comment = get_comment(stepik_api_host, token, root_id)
current_comment = get_comment(stepik_api_host, token, comment_id)

print('Found comment:', current_comment)
print('With root:', root_comment)
