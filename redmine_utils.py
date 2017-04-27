from redmine import Redmine

USER_ID_CUSTOM_FIELD = 15
COMMENT_ID_CUSTOM_FIELD = 16
STATUS_CUSTOM_FIELD = 17
DEFAULT_STATUS = 'to look at'
USEFUL_INFO_ID = 261
COMMENT_CHAIN_ID = 262

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
          {'id': USER_ID_CUSTOM_FIELD, 'value': comment.user.id}]

    if initial_status:
        cf.append({'id': STATUS_CUSTOM_FIELD, 'value': initial_status})

    issue.custom_fields = cf
    issue.category_id = category
    issue.save()

    return True, issue


def sync_comment_chain(comment):
    is_root = comment.parent is None
    created, root_issue = get_or_create_issue(comment.parent or comment, category=COMMENT_CHAIN_ID,
                                              initial_status='to look at')
    if created:
        # Here we create a new task and load all comments as chain
        for i, c in comment.all_comments.items():
            if is_root and c.id == comment.id:
                # skip self-adding as a comment
                continue

            redmine_server.issue.update(root_issue.id, notes='{} \n\n {} \n\n {}'.format(c.cleaned_text, comment.link,
                                                                                         c.user.link))
    elif not is_root:
        # Here root task already in redmine, we add only current task as a comment
        redmine_server.issue.update(root_issue.id, notes='{} \n\n {} \n\n {}'.format(comment.cleaned_text,
                                                                                     comment.link, comment.user.link))

    return True
