class GithubRequest():
    def clone(self):
        raise NotImplementedError()

    def auth(self):
        raise NotImplementedError()

    def execute(self):
        raise NotImplementedError()