def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance


def requires(precond):
    def dec(fn):
        def wrapper(self, *args):
            precond(self)
            return fn(self, *args)
        return wrapper
    return dec
