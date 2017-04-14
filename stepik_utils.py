import re

COMMENT_LINK_PATTERN = re.compile(r'https://stepik.org.*discussion=(?P<discussion>\d+)(&reply=(?P<reply>\d+))?')


def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)


def id_from_link(link):
    if not link:
        raise RuntimeError('Empty link')

    found_link = COMMENT_LINK_PATTERN.search(link).groupdict()
    discussion = found_link['discussion']
    reply = found_link['reply']
    return reply or discussion
