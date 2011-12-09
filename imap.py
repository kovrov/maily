from imaplib import IMAP4_SSL
from email.parser import HeaderParser
from email.header import make_header, decode_header
from threading import Lock
from Queue import Queue
from itertools import islice
from collections import namedtuple
import re
from PySide import QtCore as qt
import store



State = namedtuple('State', 'Undefined Pending InProgress Successful Failed')._make(range(5))

class ServiceAction(qt.QObject):
    def __init__(self, worker):
        qt.QObject.__init__(self)
        self._worker = worker
        self._serial = 0
        self._state = State.Undefined

    @qt.Slot(int, result=int)
    def getMoreConversations(self, num):
        if self._serial != 0:
            return
        self._worker.updated.connect(self._set_state)
        self._serial = self._worker.call('getMoreConversations', num)

    def _set_state(self, serial, state, text):
        if serial == self._serial:
            self._state = state
            self.on_state.emit()
            if state in (State.Successful, State.Failed):
                self._worker.updated.disconnect(self._set_state)
                self._serial = 0
                self._state = State.Undefined

    def _get_state(self):
        return self._state
    on_state = qt.Signal()
    state = qt.Property(int, _get_state, notify=on_state)



class Client(qt.QThread):
    '''Client is asynchronous interface to imap service (consider to rename)'''

    def __init__(self, store, user, pswd):
        qt.QThread.__init__(self)
        print "### Client.__init__"
        self._args = store, user, pswd
        self._queue = Queue()
        self._counter = 0
        self._counter_lock = Lock()

    def run(self):
        print "### Client.run"
        session = Session(self, *self._args)
        while True:
            print "  # _queue.get()"
            serial, method, args = self._queue.get()
            if method == 'terminate':
                self._queue.task_done()
                break
            res = getattr(session, method)(serial, *args)
            self._queue.task_done()

    def call(self, method, *args):
        print "### Client.call", method, args
        with self._counter_lock:
            self._counter += 1
            serial = self._counter
            self.updated.emit(serial, State.Pending, "put in queue")
        self._queue.put((serial, method, args))
        return serial

    updated = qt.Signal(int, int, str)



class Session(object):
    '''Session is representing partial mailbox state'''

    def __init__(self, manager, store, user, pswd):
        self.manager = manager
        self._store = store
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

    def _fetch_cached(self, hi, lo, names, pre=None):
        pre = min(max(16, (hi - lo) * 2), max(hi - lo, 64)) if pre is None else pre
        assert lo <= hi and hi - lo < pre
        fetched_hi, fetched_lo, fetched_data = self.prefetch_data
        if lo < fetched_lo or hi > fetched_hi:
            message_set = "{0:d}:{1:d}".format(max(1, hi - pre + 1), hi)
            message_parts = '('+ ' '.join(names) +')'
            typ, fetched_data = self.connection.fetch(message_set, message_parts)
            fetched_lo = int(fetched_data[0].split(None,1)[0])
            fetched_hi = int(fetched_data[-1].split(None,1)[0])
            self.prefetch_data = (fetched_hi, fetched_lo, fetched_data)
        return fetched_data[lo-fetched_lo : hi-fetched_lo+1]

    def _fetch_uids(self, count):
        # messages and threads are always sorted by server (reverse-order by uid, biggest first)
        fetch_data = self._fetch_cached(self.smallest_uid_position,
                                         self.smallest_uid_position - (count - 1),
                                         ('UID','X-GM-THRID'))
        # The data is list of strings "123 (X-GM-THRID 456 UID 789)"
        for number, data in (line.split(None,1) for line in fetch_data):
            # Transforming "(X-GM-THRID 456 UID 789)" to {"UID": 789, "X-GM-THRID": 456}
            yield dict(map(lambda i: (i[0],long(i[1])), zip(*[iter(data.strip('()').split())]*2)))
        # FIXME: not sure if this belongs here..
        self.smallest_uid_position -= len(fetch_data)

    def _search_thrid(self, thrid):
        typ, data = self.connection.uid("SEARCH", None, 'X-GM-THRID', thrid)
        return [long(i) for i in data[0].split()]

    uid_pattern = re.compile('UID (\d+)')
    def _fetch_headers(self, uids, headers):
        message_set = ','.join(map(lambda i: str(i), sorted(set(uids))))
        message_parts = '(BODY[HEADER.FIELDS ('+ ' '.join(headers) +')])'
        typ, data = self.connection.uid("FETCH", message_set, message_parts)
        for uid, raw_headers in islice(data, 0, None, 2):
            yield long(re.search(self.uid_pattern, uid).group(1)), raw_headers

    email_parser = HeaderParser()
    def getMoreConversations(self, serial, count):
        with self._store.writeLock as transaction:
            self.manager.updated.emit(serial, State.InProgress, "step 1")
            thrids = store.ConversationsDefaultDict(self._store.snapshot.conversations)
            while len(thrids.added) < count:
                n = count - len(thrids.added)
                for item in self._fetch_uids(n):
                    thrids[item['X-GM-THRID']].message_ids.append(item['UID'])
                    thrids[item['X-GM-THRID']].message_ids.sort()
                    n -= 1
                if n > 0:
                    break
            self.manager.updated.emit(serial, State.InProgress, "step 2")
            # TODO: sort thrids.added by date
            for thrid in thrids.added:
                uids = self._search_thrid(thrid)
                for uid, raw_headers in self._fetch_headers((uids[0],uids[-1]), ('SUBJECT','FROM','DATE')):
                    headers = self.email_parser.parsestr(raw_headers)
                    message = transaction.messages[uid]
                    message.subject = unicode(make_header(decode_header(headers['subject']))).replace('\r\n ',' ')
                    message.sender = unicode(make_header(decode_header(headers['from'])))
                    message.timestamp = headers['date']
                transaction.thrids[thrid].message_ids = uids
                transaction.thrids[thrid].subject = transaction.messages[uids[0]].subject
                transaction.thrids[thrid].date = transaction.messages[uids[-1]].timestamp
                self.manager.updated.emit(serial, State.InProgress, str(thrid))
                transaction.commit(block=True)
            self.manager.updated.emit(serial, State.Successful, "done")
