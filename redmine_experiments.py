from redmine import Redmine

from stepik_comments import get_comment, get_comment_ids

redmine_server = Redmine('http://demo.redmine.org', username='taery', password='abwx',
                         requests={'verify': False})
project_name = 'taery-test-project'
project = redmine_server.project.get(project_name)

link = 'https://stepik.org/lesson/%D0%A1%D0%B5%D0%BC%D0%B8%D0%BD%D0%B0%D1%80-5-%D0%9A%D1%80%D0%B8%D1%82%D0%B5%D1%80%D0%B8%D0%B8-%D1%81%D0%BE%D0%B3%D0%BB%D0%B0%D1%81%D0%B8%D1%8F-42256/step/2?discussion=356722&reply=356960'
root_id, comment_id = get_comment_ids(link)

root = get_comment(root_id)
comment = get_comment(comment_id)


# 1 - Comment id


issue = redmine_server.issue.new()
issue.project_id = project_name
issue.subject = 'User {} comment {}'.format(root.user, root_id)
issue.description = root.text
issue.custom_fields = [{'id': 1, 'value': root_id}]
issue.save()

parent_id = redmine_server.issue.filter(project_id=project_name, cf_1=root_id)[0].id


sub_issue = redmine_server.issue.new()
sub_issue.project_id = project_name
sub_issue.subject = 'User {} comment {}'.format(comment.user, comment_id)
sub_issue.description = comment.text
sub_issue.parent_issue_id = parent_id
sub_issue.custom_fields = [{'id': 1, 'value': comment_id}]
sub_issue.save()

# parent not work?

# try relations

# problem with auth
# relation = redmine_server.issue_relation.create(issue_id=sub_issue.id, issue_to_id=sub_issue.parent_issue_id,
#                                                 relation_type='follows')

