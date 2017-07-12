# логинимся
# выгружаем задачи, помечанные to look at -- ? обдумать
# находим задачу на степике по задаче на редмайне
# проверяем, что notes соответствуют комментариям на степике
import configparser

from api_objects import init_stepik, Comment
from redmine_utils import init_redmine, get_to_look_at_issues_from_project, \
     get_link_to_comment_from_issue, get_all_comments_from_issue_notes, update_chain

SETTINGS_FILE_PATH = 'settings.properties'


def init():
    if not init_stepik(config['stepik']['api_host'], config['stepik']['client_id'],
                       config['stepik']['client_secret']):
        raise RuntimeError('Cannot connect to stepik instance')

    if not init_redmine(config['redmine']['api_host'], config['redmine']['api_key'], config['redmine']['project']):
        raise RuntimeError('Cannot connect to redmine server')


def validate_issues():
    for issue in issues:
        notes = get_all_comments_from_issue_notes(issue.journals)
        link = get_link_to_comment_from_issue(issue)
        comments = Comment.get_comments_text(link)
        print(notes)
        # if len(notes) != len(comments):
        #     update_chain(issue, Comment.retrieve(link=link))
        # else:
        #     print('issue {} is correct'.format(issue.id))


def is_notes_corresponds_to_discussion(notes, comments):
    print(notes)
    print(comments)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(SETTINGS_FILE_PATH)
    init()
    issues = get_to_look_at_issues_from_project()
    validate_issues()

