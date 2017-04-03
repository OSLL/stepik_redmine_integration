class Comment:
    def __init__(self, comment_id, user, text, link):
        super().__init__()
        self.id = comment_id
        self.user = user
        self.text = text
        self.link = link

    def __str__(self, *args, **kwargs):
        return 'User {} comments[{}]: {}'.format(self.user, self.id, self.text)


class User:
    def __init__(self, user_id):
        super().__init__()
        self.id = user_id

    def __str__(self, *args, **kwargs):
        return str(self.id)
