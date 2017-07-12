import json

from stepik_api_requestor import StepikAPIRequestor
from stepik_utils import remove_html_tags, ids_from_link, link_from_text

api = None


def init_stepik(api_url, client_id, client_secret):
    global api

    api = StepikAPIRequestor(api_url)
    return api.connect(client_id, client_secret)


def convert_to_stepik_object(object_name, resp):
    types = {
        'comments': Comment,
        'users': User,
        'user': User,
        'notifications': Notification,
        'meta': MetaInf
    }
    if isinstance(resp, list):
        return list(filter(None, [convert_to_stepik_object(object_name, i) for i in resp]))
    elif isinstance(resp, dict):
        klass = types.get(object_name, None)
        return klass.construct_from(resp) if klass else None
    else:
        return resp


def map_retrieved_objects(response):
    res = {}
    for k, v in response.items():
        transformed = convert_to_stepik_object(k, v)
        if transformed:
            res[k] = transformed
    return res


class StepikObject(dict):
    def __init__(self, id=None, **params):
        super(StepikObject, self).__init__()
        self._retrieve_params = params

        if id:
            self['id'] = id

    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v
        return None

    @classmethod
    def construct_from(cls, values):
        instance = cls(values.get('id'))
        instance.refresh_from(values)
        return instance

    def refresh_from(self, values):
        for k, v in values.items():
            super(StepikObject, self).__setitem__(k, convert_to_stepik_object(k, v))

    @classmethod
    def api_base(cls):
        return None

    def request(self, method, url, params=None, json_data=None):
        if params is None:
            params = self._retrieve_params
        response = api.request(method, url, params, json_data)
        return map_retrieved_objects(response)

    def __str__(self):
        return json.dumps(self, indent=2, ensure_ascii=False)


class APIResource(StepikObject):
    @classmethod
    def retrieve(cls, id, **params):
        instance = cls(id, **params)
        instance.refresh()
        return instance

    def refresh(self):
        values = self.request('get', self.instance_url())
        current_resource = list(filter(lambda r: r.id == self.id, values.get(self.resource_name())))
        if current_resource:
            self.refresh_from(current_resource[0])
        return self

    @classmethod
    def base_url(cls):
        return '/api/{}'.format(cls.resource_name())

    @classmethod
    def resource_name(cls):
        raise NotImplementedError

    def instance_url(self, id=None):
        id = id or self.get('id')
        if not id:
            raise Exception('Empty object id')
        base = self.base_url()
        return "{}/{}".format(base, id)


class ListableAPIResource(APIResource):
    @classmethod
    def auto_paging_iter(cls, **params):
        return cls.list(**params).auto_paging()

    @classmethod
    def list(cls, **params):
        url = cls.base_url()
        response = api.request('get', url, params)
        stepik_object = convert_to_stepik_object(cls.resource_name(), response)
        stepik_object._retrieve_params = params
        return stepik_object


class ListObject(StepikObject):
    def list(self, **params):
        return self.request('get', self['url'], params)

    def auto_paging(self):
        page = self
        params = dict(self._retrieve_params)
        while True:
            for item in page:
                yield item

            meta = getattr(page, 'meta', None)
            if not meta or not meta.has_next:
                return

            params['page'] = meta.page + 1
            page = self.list(**params)

    def retrieve(self, id, **params):
        base = self.get('url')
        url = "{}/{}".format(base, id)

        return self.request('get', url, params)

    def __iter__(self):
        return getattr(self, self.__class__.resource_name(), []).__iter__()


class UpdatableAPIResource(APIResource):
    def save(self, json_data):
        self.refresh_from(self.request('put', self.instance_url(), json_data=json_data))
        return self


class CreatableAPIResource(APIResource):
    def create(self, json_data, **params):
        self.refresh_from(self.request('post', self.base_url(), params, json_data=json_data))
        return self


class MetaInf(dict):
    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v
        return None

    @classmethod
    def construct_from(cls, values):
        return cls(values)


class Notification(ListableAPIResource, ListObject, UpdatableAPIResource):
    @classmethod
    def resource_name(cls):
        return 'notifications'

    def make_read(self):
        self.save({'notification': {'is_unread': False}})
        return True


class User(APIResource):
    @classmethod
    def resource_name(cls):
        return 'users'

    @property
    def link(self):
        return '{}/users/{}'.format(api.api_base, self.id)


class Comment(CreatableAPIResource):
    def __init__(self, id=None, **params):
        super().__init__(id, **params)
        self.all_comments = {}
        self.parent = None
        self.step_url = ''

    @classmethod
    def resource_name(cls):
        return 'comments'

    @property
    def cleaned_text(self):
        return remove_html_tags(self.text)

    @property
    def link(self):
        return '{}{}?discussion={}&thread={}'.format(api.api_base, self.step_url,
                                                     '{}&reply={}'.format(self.parent.id, self.id)
                                                     if self.parent else '{}'.format(self.id), self.thread)

    def refresh(self):
        def transform(c):
            comment = convert_to_stepik_object(self.resource_name(), c)
            comment.refresh_from({'user': users.get(comment.user)})
            comment.step_url = self.step_url
            return comment.id, comment

        parent = None
        current = self.id
        if 'parent' in self._retrieve_params:
            parent = self._retrieve_params.pop('parent')

        if 'step_url' in self._retrieve_params:
            self.step_url = self._retrieve_params.pop('step_url')

        values = self.request('get', self.instance_url(parent))

        chain = values[self.resource_name()]

        users = {u['id']: u for u in values['users']}
        all_comments = dict(map(transform, chain))
        self.refresh_from(all_comments.get(current))

        if self.parent:
            self.parent = all_comments.pop(self.parent)
        self.all_comments = all_comments
        return self


    @classmethod
    def retrieve(cls, id=None, link=None, **params):
        parent = None
        link_prefix = ''
        if not id:
            link_prefix, parent, id = ids_from_link(link)

        comment = super().retrieve(id, parent=parent, step_url=link_prefix, **params)
        return comment


    @classmethod
    def get_chain(cls, notification):
        comment_link = link_from_text(api.api_base, notification.html_text)
        return cls.retrieve(link=comment_link)


    def reply_to(self, text):
        return self.create({'comment': {'target': self.target, 'parent': self.id,
                                        'thread': self.thread,
                                        'text': text}})

    @classmethod
    def get_comments_text(cls, link):
        comment = cls.retrieve(link=link)
        comments = []
        for value in comment['all_comments'].values():
            comments.append(remove_html_tags(value['text']))
        return comments
