import json

from stepik_api_requestor import StepikAPIRequestor
from stepik_utils import remove_html_tags, id_from_link

api = None


def init_stepik(api_url, client_id, client_secret):
    global api

    api = StepikAPIRequestor(api_url)
    return api.connect(client_id, client_secret)


def convert_to_stepik_object(object_name, resp):
    types = {
        'comments': Comment,
        'users': User,
        'user': User
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

        # self._unsaved_values = set()
        # self._transient_values = set()

        self._retrieve_params = params
        self._previous = None

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

        self._previous = values

    @classmethod
    def api_base(cls):
        return None

    def request(self, method, url, params=None):
        if params is None:
            params = self._retrieve_params

        response = api.request(method, url, params)

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

    def instance_url(self):
        id = self.get('id')
        if not id:
            raise Exception('Empty object id')
        base = self.base_url()
        return "{}/{}".format(base, id)


class ListObject(StepikObject):
    def list(self, **params):
        return self.request('get', self['url'], params)

    def auto_paging_iter(self):
        page = self
        params = dict(self._retrieve_params)

        while True:
            item_id = None
            for item in page:
                item_id = item.get('id', None)
                yield item

            if not getattr(page, 'has_more', False) or item_id is None:
                return

            params['starting_after'] = item_id
            page = self.list(**params)

    def retrieve(self, id, **params):
        base = self.get('url')
        url = "{}/{}".format(base, id)

        return self.request('get', url, params)

    def __iter__(self):
        return getattr(self, 'data', []).__iter__()


class ListableAPIResource(APIResource):
    @classmethod
    def auto_paging_iter(cls, **params):
        return cls.list(**params).auto_paging_iter()

    @classmethod
    def list(cls, **params):
        url = cls.base_url()
        response = api.request('get', url, params)
        stepik_object = map_retrieved_objects(response)
        stepik_object._retrieve_params = params
        return stepik_object


class Comment(ListableAPIResource):
    @classmethod
    def resource_name(cls):
        return 'comments'

    @property
    def cleaned_text(self):
        return remove_html_tags(self.text)

    def refresh(self):
        values = self.request('get', self.instance_url())
        current_resource = list(filter(lambda r: r.id == self.id, values.get(self.resource_name())))
        if current_resource:
            self.refresh_from(current_resource[0])
        # Todo bug wrong user
        user = values['users'][0]
        self.refresh_from({'user': user})
        return self

    @classmethod
    def retrieve(cls, id=None, link=None, **params):
        if not id:
            id = int(id_from_link(link))

        comment = super().retrieve(id, **params)
        comment.link = link
        return comment


class User(APIResource):
    @classmethod
    def resource_name(cls):
        return 'users'

    @property
    def link(self):
        return '{}/users/{}'.format(api.api_base, self.id)
