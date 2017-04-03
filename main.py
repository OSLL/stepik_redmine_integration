import configparser

import requests
from redmine import Redmine

from google_utlis import load_links_from_google
from stepik_utils import get_comment_ids, get_comment

config = configparser.ConfigParser()
config.read('settings.properties')

client_id = config['stepik']['client_id']
client_secret = config['stepik']['client_secret']
stepik_api_host = config['stepik']['api_host']

redmine_host = config['redmine']['api_host']
redmine_api_key = config['redmine']['api_key']
project_name = config['redmine']['project']

# Load all urls from google file (TODO check color status - api cannot do this?)
sheet_id = config['google']['sheet_id']
sheet_range = config['google']['sheet_range']

# Transform links to ids
all_links = load_links_from_google(sheet_id, sheet_range)
all_ids = sorted(map(lambda x: get_comment_ids(x), all_links))

# Connect to stepik
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepik.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth)
token = resp.json().get('access_token')
if not token:
    raise RuntimeWarning('Client id/secret is probably incorrect')

# Connect to redmine
redmine_server = Redmine(redmine_host, key=redmine_api_key)

project = redmine_server.project.get(project_name)

for parent_id, current_id in all_ids:
    parent = get_comment(stepik_api_host, token, parent_id)
    current = get_comment(stepik_api_host, token, current_id)

    if not parent:
        print("skip", parent_id)
        continue

    if not current:
        print("skip", current_id)
        continue

    parent_task = redmine_server.issue.filter(project_id=project_name, cf_16=parent_id)
    parent_task_id = parent_task[0].id if parent_task else None

    current_task = redmine_server.issue.filter(project_id=project_name, cf_16=current_id)
    if current_task:
        print("skip", current_id, current_task.resources)
        continue

    sub_issue = redmine_server.issue.new()
    sub_issue.project_id = project_name
    sub_issue.subject = 'User {} comment {}'.format(current.user, current_id)
    sub_issue.description = current.text
    sub_issue.custom_fields = [{'id': 16, 'value': current_id}, {'id': 15, 'value': current.user.id}]
    sub_issue.save()

    if parent_task_id:
        redmine_server.issue_relation.create(issue_id=sub_issue.id, issue_to_id=parent_task_id,
                                             relation_type='follows')

