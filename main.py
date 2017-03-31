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

# issue = redmine_server.issue.get(resource_id=8055)  # TODO custom fields not work
# for r in issue.custom_fields.values():
#     print(r)


for parent_id, current_id in all_ids:
    parent = get_comment(stepik_api_host, token, parent_id)
    current = get_comment(stepik_api_host, token, current_id)

    # issue = redmine_server.issue.new()
    # issue.project_id = project_name
    # issue.subject = 'User {} comment {}'.format(parent.user, parent_id)
    # issue.description = parent.text
    # issue.custom_fields = [{'id': 1, 'value': parent_id}]  # TODO not work?
    # issue.save()

    parent_task = redmine_server.issue.filter(project_id=project_name, cf_1=parent_id)
    parent_task_id = parent_task[0].id if parent_task else None

    current_task = redmine_server.issue.filter(project_id=project_name, cf_1=current_id)
    if current_task:
        print("skip", current_id, current_task.resources)
        continue
    print('handle', current_id)
    sub_issue = redmine_server.issue.new()
    sub_issue.project_id = project_name
    sub_issue.subject = 'User {} comment {}'.format(current.user, current_id)
    sub_issue.description = current.text
    # TODO: parent not work?
    # sub_issue.parent_issue_id = parent_id
    sub_issue.custom_fields = [{'id': 1, 'value': current_id}]
    sub_issue.save()

    if parent_task_id:
        redmine_server.issue_relation.create(issue_id=sub_issue.id, issue_to_id=parent_task_id,
                                             relation_type='follows')
