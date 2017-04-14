from redmine import Redmine

USER_ID_CUSTOM_FIELD = 15
COMMENT_ID_CUSTOM_FIELD = 16
USEFUL_INFO_ID = 261

redmine_server = None
project_name = None


def init_redmine(redmine_host, redmine_api_key, redmine_project_name):
    global redmine_server, project_name
    redmine_server = Redmine(redmine_host, key=redmine_api_key)
    project_name = redmine_project_name
    return True


def get_or_create_issue(comment):
    if not redmine_server:
        print('Init redmine connection before creating task')
        return

    current_issue = redmine_server.issue.filter(project_id=project_name, cf_16=comment.id)
    if current_issue:
        print('skip creating for', comment.id)
        return current_issue

    issue = redmine_server.issue.new()
    issue.project_id = project_name
    issue.subject = 'User {} comment {}'.format(comment.user.id, comment.id)
    issue.description = '{} \n\n {} \n\n {}'.format(comment.cleaned_text, comment.link, comment.user.link)
    issue.custom_fields = [{'id': COMMENT_ID_CUSTOM_FIELD, 'value': comment.id},
                           {'id': USER_ID_CUSTOM_FIELD, 'value': comment.user.id}]
    issue.category_id = USEFUL_INFO_ID
    issue.save()

    return issue
