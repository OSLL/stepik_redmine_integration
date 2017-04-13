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


sheet_id = config['google']['sheet_id']
sheet_range = config['google']['sheet_range']

# Load all urls from google file (TODO check color status - api cannot do this?)
all_links = load_links_from_google(sheet_id, sheet_range)
# Transform links to ids
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


def create_new_task(comment):
    issue = redmine_server.issue.new()
    issue.project_id = project_name
    issue.subject = 'User {} comment {}'.format(comment.user, current_id)
    issue.description = '{} \n\n {} \n\n {}/users/{}'.format(comment.text, comment.link,
                                                             stepik_api_host, comment.user.id)
    issue.custom_fields = [{'id': 16, 'value': current_id}, {'id': 15, 'value': comment.user.id}]
    issue.save()

    return issue


for parent_id, current_id, link in all_ids:
    # Try to load root and current comments
    # parent = get_comment(stepik_api_host, token, parent_id)
    current = get_comment(stepik_api_host, token, current_id, link)

    if not current:
        print("skip", current_id)
        continue

    # search existing in redmine
    parent_task = redmine_server.issue.filter(project_id=project_name, cf_16=parent_id)
    parent_task_id = parent_task[0].id if parent_task else None

    current_task = redmine_server.issue.filter(project_id=project_name, cf_16=current_id)
    if current_task:
        print("Already created for:", current_id)
        continue

    # Create new task if not found
    sub_issue = create_new_task(current)

    if parent_task_id:
        redmine_server.issue_relation.create(issue_id=sub_issue.id, issue_to_id=parent_task_id,
                                             relation_type='follows')

