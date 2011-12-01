from imaplib import IMAP4_SSL
from threading import Thread
from Queue import Queue



class Client(Thread):
    '''Client is asynchronous interface to imap service (consider to rename)'''

    def __init__(self, store, user, pswd):
        Thread.__init__(self)
        print "### Client.__init__"
        self.__args = user, pswd
        self.__queue = Queue()
        self.__store = store

    def run(self):
        print "### Client.run"
        session = Session(self.__store, *self.__args)
        while True:
            print "  # __queue.get()"
            method, args = self.__queue.get()
            if method is 'terminate':
                self.__queue.task_done()
                break
            res = getattr(session, method)(*args)
            self.__queue.task_done()

    def call(self, method, *args):
        print "### Client.call"
        self.__queue.put((method, args))



class Session(object):
    '''Session is representing partial mailbox state'''

    def __init__(self, store, user, pswd):
        self.__store = store

        self.smallest_uid_position = 0  # zero is invalid

        self.connection = IMAP4_SSL("imap.gmail.com")
        self.connection.login(user, pswd)
        typ, messages_count = self.connection.select()
        self.smallest_uid_position = int(messages_count[0])
        self.prefetch_data = (-1,-1,[])

    def __del__(self):
        # TODO: serialize?
        self.connection.close()
        self.connection.logout()

    def __fetch_cached(self, hi, lo, names, pre=64):
        assert lo <= hi and hi - lo < pre
        fetched_hi, fetched_lo, fetched_data = self.prefetch_data
        if lo < fetched_lo or hi > fetched_hi:
            message_set = "{0:d}:{1:d}".format(max(1, hi - pre + 1), hi)
            message_parts = '('+ ' '.join(names) +')'
            print 'FETCH', message_set, message_parts
            typ, fetched_data = self.connection.fetch(message_set, message_parts)
            fetched_lo = int(fetched_data[0].split(None,1)[0])
            fetched_hi = int(fetched_data[-1].split(None,1)[0])
            self.prefetch_data = (fetched_hi, fetched_lo, fetched_data)
        return fetched_data[lo-fetched_lo : hi-fetched_lo+1]

    def __load_messages(self, count, transaction):
        # messages and threads are always sorted by server (reverse-order by uid, biggest first)
        fetch_data = self.__fetch_cached(self.smallest_uid_position,
                                         self.smallest_uid_position - (count - 1),
                                         ('UID','X-GM-THRID'))
        # The data is list of strings "123 (X-GM-THRID 456 UID 789)"
        for number, data in (line.split(None,1) for line in reversed(fetch_data)):
            # Transforming "(X-GM-THRID 456 UID 789)" to {"UID": 789, "X-GM-THRID": 456}
            item = dict(map(lambda i: (i[0],int(i[1])), zip(*[iter(data.strip('()').split())]*2)))
            # addMessage will add thread to transaction if needed
            transaction.addMessage(message_id=item['UID'], thread_id=item['X-GM-THRID'])
        # FIXME: not sure if this belongs here..
        self.smallest_uid_position -= len(fetch_data)
        return len(fetch_data)

    def getMoreConversations(self, count):
        with self.__store.writeLock as transaction:
            while len(transaction.conversations.added) < count:
                n = count - len(transaction.conversations.added)
                if n > self.__load_messages(n, transaction):
                    break
            transaction.commit(block=True)
