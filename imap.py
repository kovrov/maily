import socket
from imaplib import IMAP4_SSL, IMAP4
from email.parser import HeaderParser
from email.header import make_header, decode_header
from email.utils import mktime_tz, parsedate_tz
from threading import Lock
from Queue import Queue
from itertools import islice
from collections import namedtuple
import re
from PySide import QtCore as qt
import store
from utils import singleton, requires



State = namedtuple('State', 'Undefined Pending InProgress Successful Failed')._make(range(5))

class ServiceAction(qt.QObject):
    def __init__(self, parent=None):
        qt.QObject.__init__(self, parent)
        self._dispatcher = None
        self._serial = 0
        self._state = State.Undefined
        self._progress = float()

    @qt.Slot(int)
    def getMoreConversations(self, num):
        if self._serial != 0:
            return
        if self._dispatcher is None:
            self._dispatcher = ActionDispatcher()
        self._dispatcher.updated.connect(self._set_state)
        self._dispatcher.progress.connect(self._set_progress)
        self._serial = self._dispatcher.call('getMoreConversations', num)

    def _set_state(self, serial, state, text):
        if serial == self._serial:
            self._state = state
            self.stateChanged.emit()
            if state in (State.Successful, State.Failed):
                self._dispatcher.updated.disconnect(self._set_state)
                self._dispatcher.progress.disconnect(self._set_progress)
                # TODO: timer
                self._serial = 0
                self._state = State.Undefined
                self.stateChanged.emit()
                self._progress = float()
                self.on_progress.emit()

    def _get_state(self):
        return self._state
    stateChanged = qt.Signal()
    state = qt.Property(int, _get_state, notify=stateChanged)

    def _set_progress(self, serial, progress):
        if serial == self._serial:
            self._progress = progress
            self.on_progress.emit()

    def _get_progress(self):
        return self._progress
    on_progress = qt.Signal()
    progress = qt.Property(float, _get_progress, notify=on_progress)



@singleton
class ActionDispatcher(qt.QObject):
    '''ActionDispatcher is asynchronous interface to imap service (consider to rename)'''

    def __init__(self):
        qt.QObject.__init__(self)
        self._queue = Queue()
        self._counter = 0
        self._counter_lock = Lock()
        thread = qt.QThread(self)
        self.moveToThread(thread)
        thread.started.connect(self.run)
        thread.start()

    @qt.Slot()
    def run(self):
        app = qt.QCoreApplication.instance()
        app.aboutToQuit.connect(lambda: self.call('terminate'))
        processor = ActionProcessor(self)
        while True:
            serial, method, args = self._queue.get()
            if method == 'terminate':
                self._queue.task_done()
                break
            try:
                res = getattr(processor, method)(serial, *args)
            except SessionError as e:
                self.updated.emit(serial, State.Failed, e.message)
            self._queue.task_done()

    def call(self, method, *args):
        with self._counter_lock:
            self._counter += 1
            serial = self._counter
            self.updated.emit(serial, State.Pending, "put in queue")
        self._queue.put((serial, method, args))
        return serial

    updated = qt.Signal(int, int, str)
    progress = qt.Signal(int, float)



class SessionError(Exception):
    def __init__(self, message):
        self.message = message



class ActionProcessor(object):
    '''ActionProcessor is representing partial mailbox state'''

    def __init__(self, manager):
        self.manager = manager
        self._store = store.Store()
        self.smallest_uid_position = 0  # zero is invalid
        self.prefetch_data = (-1,-1,[])
        self.connection = None
        try:
            self.online()
        except SessionError:
            pass

    def __del__(self):
        # TODO: serialize?
        if self.connection:
            self.connection.close()
            self.connection.logout()

    def online(self):
        if self.connection:
            return True
        try:
            self.connection = IMAP4_SSL("imap.gmail.com")
        except socket.gaierror:
            raise SessionError('could not resolve server name')
        except socket.error:
            raise SessionError('could not connect to server')
        try:
            self.connection.login('xxx', 'yyy')
        except IMAP4.error as e:
            self.connection.shutdown()
            self.connection = None
            raise SessionError(e.message)
        typ, messages_count = self.connection.select()
        if typ == 'NO':
            self.connection.logout()
            self.connection = None
            raise SessionError(messages_count[0])
        self.smallest_uid_position = int(messages_count[0])

    @requires(online)
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

    @requires(online)
    def _search_thrid(self, thrid):
        typ, data = self.connection.uid("SEARCH", None, 'X-GM-THRID', thrid)
        return [long(i) for i in data[0].split()]

    uid_pattern = re.compile('UID (\d+)')
    @requires(online)
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
            for i, thrid in enumerate(thrids.added):
                uids = self._search_thrid(thrid)
                for uid, raw_headers in self._fetch_headers((uids[0],uids[-1]), ('SUBJECT','FROM','DATE')):
                    headers = self.email_parser.parsestr(raw_headers)
                    message = transaction.messages[uid]
                    message.subject = unicode(make_header(decode_header(headers['subject']))).replace('\r\n ',' ')
                    message.sender = unicode(make_header(decode_header(headers['from'])))
                    message.timestamp = mktime_tz(parsedate_tz(headers['date']))
                transaction.thrids[thrid].message_ids = uids
                transaction.thrids[thrid].subject = transaction.messages[uids[0]].subject
                transaction.thrids[thrid].date = transaction.messages[uids[-1]].timestamp
                self.manager.progress.emit(serial, float(i+1) / len(thrids.added))
                transaction.commit(block=True)
            self.manager.updated.emit(serial, State.Successful, "done")
