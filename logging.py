'''
Monkey-patching various library routines for logging calls.
'''



def logged_fetch(fn):
    def wrapper(self, message_set, message_parts):
        print "FETCH", message_set, message_parts
        return fn(self, message_set, message_parts)
    return wrapper

def logged_search(fn):
    def wrapper(self, charset, *criteria):
        print "SEARCH", charset, " ".join(str(i) for i in criteria if i is not None)
        fn(self, charset, *criteria)
    return wrapper

def logged_uid(fn):
    def wrapper(self, command, *args):
        print "UID", command, " ".join(str(i) for i in args if i is not None)
        return fn(self, command, *args)
    return wrapper

# IMAP4_SSL.fetch = logged_fetch(IMAP4_SSL.fetch)
# IMAP4_SSL.search = logged_search(IMAP4_SSL.search)
# IMAP4_SSL.uid = logged_uid(IMAP4_SSL.uid)
