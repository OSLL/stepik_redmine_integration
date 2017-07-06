from redmine import Redmine
import requests

USER_ID_CUSTOM_FIELD = 15
COMMENT_ID_CUSTOM_FIELD = 16
STATUS_CUSTOM_FIELD = 17
ON_STEPIK_FIELD = 18
MUTED_STATUS = 'muted'
ANSWERED_STATUS = 'answered'
DEFAULT_STATUS = 'to look at'
USEFUL_INFO_ID = 261
COMMENT_CHAIN_ID = 262
ASSIGNED_TO_ID = 5
QUERY_ID_AJILE = 215

COMMENT_ID = 'comment_id'
COMMENT_STATUS = 'comment_status'
USER_ID = 'user_id'
JOURNAL_ATTRIBUTES = '_attributes'
NOTES = 'notes'
USER = 'user'
ON_STEPIK = 'on_stepik'
ID = 'id'
VALUE = 'value'
RESOURCES = 'resources'
NAME = 'name'
YES = '1'
NO = '0'


possible_users = [330, 5, 43]

redmine_server = None
project_name = None


def init_redmine(redmine_host, redmine_api_key, redmine_project_name):
    global redmine_server, project_name
    redmine_server = Redmine(redmine_host, key=redmine_api_key)
    project_name = redmine_project_name
    return True


def get_server():
    return redmine_server


def get_or_create_issue(comment, category=USEFUL_INFO_ID, initial_status=None):
    if not redmine_server:
        print('Init redmine connection before creating task')
        return

    current_issue = redmine_server.issue.filter(project_id=project_name, cf_16=comment.id)
    if current_issue:
        return False, current_issue[0]

    issue = redmine_server.issue.new()
    issue.project_id = project_name
    issue.subject = 'User {} comment {}'.format(comment.user.id, comment.id)
    issue.description = '{} \n\n {} \n\n {}'.format(comment.cleaned_text, comment.link, comment.user.link)

    cf = [{'id': COMMENT_ID_CUSTOM_FIELD, 'value': comment.id},
          {'id': USER_ID_CUSTOM_FIELD, 'value': comment.user.id},
          {'id': ON_STEPIK, 'value': NO}]

    if initial_status:
        cf.append({'id': STATUS_CUSTOM_FIELD, 'value': initial_status})

    issue.custom_fields = cf
    issue.category_id = category
    issue.assigned_to_id = ASSIGNED_TO_ID
    issue.save()

    return True, issue


def sync_comment_chain(comment):
    is_root = comment.parent is None
    created, root_issue = get_or_create_issue(comment.parent or comment, category=COMMENT_CHAIN_ID,
                                              initial_status=DEFAULT_STATUS)
    if not is_root:
        status = root_issue.custom_fields.get(STATUS_CUSTOM_FIELD).value
        if status == MUTED_STATUS:
            # skip muted comments
            return True

        # Here root task already in redmine, we add only current task as a comment
        redmine_server.issue.update(root_issue.id, notes='{} \n\n {} \n\n {}'.format(comment.cleaned_text,
                                                                                     comment.link, comment.user.link))
        if status == ANSWERED_STATUS:
            # Change answered on to look at with new comments
            redmine_server.issue.update(root_issue.id, custom_fields=[{ID: STATUS_CUSTOM_FIELD,
                                                                       VALUE: DEFAULT_STATUS}])

    return True


def set_issue_answered_on_stepik_status(issue):
    redmine_server.issue.update(issue.id, custom_fields=[{ID: ON_STEPIK_FIELD, VALUE: YES}])


def get_data_from_issue_to_answer_on_stepik(issue):
    list_resources = issue.custom_fields[RESOURCES]
    comment_id = get_cf_value_by_name(list_resources, COMMENT_ID)
    user_id = get_cf_value_by_name(list_resources, USER_ID)
    journals = issue.journals
    journal_attr = journals[len(journals)-1][JOURNAL_ATTRIBUTES]
    note = ''
    if journal_attr[USER][ID] in possible_users and journal_attr[NOTES] != '':
        note = journal_attr[NOTES]
    return comment_id, user_id, note


def get_cf_value_by_name(list_resources, name):
    for resource in list_resources:
        if resource[NAME] == name:
            return resource[VALUE]


def get_answered_issues_from_project():
    if not redmine_server:
        print('Init redmine connection before creating task')
        return
    return redmine_server.issue.filter(project_id=project_name, cf_17=ANSWERED_STATUS, cf_18=NO)
