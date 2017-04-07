# 2. Get a token
import re
import requests

from api_objects import User, Comment


# 3. Call API (https://stepik.org/api/docs/) using this token.
# Generator definition for iterating over pages
def list_pages(api_url, objects, token):
    has_next = True
    page = 1
    if '?' in api_url:
        connector = '&'
    else:
        connector = '?'
    while has_next:
        response = requests.get(api_url + '{}page={}'.format(connector, page),
                                headers={'Authorization': 'Bearer ' + token}).json()
        # Hack for permission denied
        if 'meta' not in response:
            return []
        yield [{obj: response[obj] for obj in objects}]
        page += 1
        has_next = response['meta']['has_next']


def fetch_object(api_host, token, obj_class, query_string='', additional_objects=None):
    api_url = '{}/api/{}{}'.format(api_host, obj_class, query_string)

    if additional_objects:
        additional_objects.append(obj_class)
    else:
        additional_objects = [obj_class]

    response = list_pages(api_url, additional_objects, token)
    return [obj for page in response for obj in page]       # Example of using generator


def get_comment(api_host, token, comment_id, link_to_comment):
    comment = fetch_object(api_host, token, 'comments', '/{}'.format(comment_id), ['users'])

    if not comment:
        return None

    user = User(comment[0]['users'][0]['id'])
    comment = Comment(comment[0]['comments'][0]['id'], user, remove_html_tags(comment[0]['comments'][0]['text']),
                      link_to_comment)
    return comment


def get_comment_ids(link_to_comment):
    pattern = re.compile(r'https://stepik.org.*discussion=(?P<discussion>\d+)(&reply=(?P<reply>\d+))?')
    found_link = pattern.search(link_to_comment).groupdict()
    discussion = found_link['discussion']
    reply = found_link['reply']
    return discussion, reply or discussion, link_to_comment


def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)
