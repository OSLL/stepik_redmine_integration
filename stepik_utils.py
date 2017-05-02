import re
from urllib.parse import unquote

COMMENT_LINK_PATTERN = re.compile(r'.*(?P<prefix>\/lesson.*?step\/\d*)\?discussion=(?P<discussion>\d+)(.*reply=(?P<reply>\d+))?')
LINK_PATTERN = re.compile(r'href=\"(.*?)\"')


def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)


def ids_from_link(link):
    if not link:
        raise RuntimeError('Empty link')

    found_link = COMMENT_LINK_PATTERN.search(link).groupdict()
    discussion = found_link['discussion']
    reply = found_link['reply']
    link_prefix = found_link['prefix']
    return link_prefix, int(discussion), int(reply or discussion)


def link_from_text(base, text):
    links = LINK_PATTERN.findall(text)
    return '{}{}'.format(base, unquote(links[-1]))
