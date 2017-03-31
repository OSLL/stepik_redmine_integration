import configparser

import requests
from redmine import Redmine

from stepik_utils import get_comment, get_comment_ids

config = configparser.ConfigParser()
config.read('settings.properties')

client_id = config['stepik']['client_id']
client_secret = config['stepik']['client_secret']
stepik_api_host = config['stepik']['api_host']

redmine_host = config['redmine']['api_host']
redmine_api_key = config['redmine']['api_key']
project_name = config['redmine']['project']

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

redmine_server = Redmine(redmine_host, key=redmine_api_key)

project = redmine_server.project.get(project_name)

# 1 - Comment id

issue = redmine_server.issue.new()
issue.project_id = project_name
issue.subject = 'User {} comment {}'.format(root_comment.user, root_id)
issue.description = root_comment.text
issue.custom_fields = [{'id': 1, 'value': root_id}]
issue.save()

parent_id = redmine_server.issue.filter(project_id=project_name, cf_1=root_id)[0].id


sub_issue = redmine_server.issue.new()
sub_issue.project_id = project_name
sub_issue.subject = 'User {} comment {}'.format(current_comment.user, comment_id)
sub_issue.description = current_comment.text
# TODO: parent not work?
sub_issue.parent_issue_id = parent_id
sub_issue.custom_fields = [{'id': 1, 'value': comment_id}]
sub_issue.save()



# try relations
relation = redmine_server.issue_relation.create(issue_id=sub_issue.id, issue_to_id=sub_issue.parent_issue_id,
                                                relation_type='follows')

