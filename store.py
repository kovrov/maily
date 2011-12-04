from PySide import QtCore as qt
from threading import Lock
from collections import namedtuple


'''
Main concepts:
* Immutable data to share between threads (no copying, no read-locking)
* Atomic snapshots of data (versions)
* Transactional atomic changes to data (new snapshot)
* Write-locking to prevent concurrent commit conflicts
* Notification of data changes (new snapshot + change description)
Worth consideration:
* Asynchronous write?
* Ability to serialize/deserialize itself?
'''


Snapshot = namedtuple('Snapshot',['conversations','messages'])


def b_index(a, key):
    lo, hi = 0, len(a)
    if lo < hi and key == a[lo].id:
        return lo
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if key < a[mid].id:
            hi = mid
        else:
            lo = mid
        if key == a[lo].id:
            return lo
    raise KeyError(key)


class Store(qt.QObject):
    def __init__(self):
        qt.QObject.__init__(self)
        self.writeLock = TransactionLock(self)
        self.snapshot = Snapshot(tuple(), tuple())
    conversationsChanged = qt.Signal(tuple, tuple)



class TransactionLock(object):
    def __init__(self, store):
        self._store = store
        self._lock = Lock()
    def __enter__(self):
        self._lock.acquire()
        return Transaction(self._store)
    def __exit__(self, *args):
        self._lock.release()



def _merge(original, modified, added, Type):
    if modified:
        original = [Conversation(*modified[i.id]) if i.id in modified else i for i in original]
    else:
        original = list(original)
    return tuple(sorted(original + [Type(*i) for i in added.values()]))

class Transaction(object):
    '''
    * Transaction data is combined with store snapshot
    '''
    def __init__(self, store):
        self._store = store
        self._snapshot = store.snapshot
        self.thrids = TransactionField(self._snapshot.conversations, MutableConversation)

    def add_uid(self, message_id, thread_id):
        self.thrids[thread_id].message_ids.append(message_id)
        self.thrids[thread_id].message_ids.sort()

    def commit(self, block=True):
        new_conversations = _merge(self._snapshot.conversations, self.thrids.modified, self.thrids.added, Conversation)
        self._store.snapshot = Snapshot(conversations=new_conversations, messages=self._snapshot.messages)
        self._store.conversationsChanged.emit(self._store.snapshot, (sorted(self.thrids.modified.keys()),
                                                                       sorted(self.thrids.added.keys())))
        self.__init__(self._store)



class TransactionField(object):
    def __init__(self, original, MutableType):
        self._original = original
        self._MutableType = MutableType
        self.added = {}
        self.modified = {}
        self._removed = []
    def __getitem__(self, key):
        if key in self.added:
            return self.added[key]
        if key in self.modified:
            return self.modified[key]
        try:
            self.modified[key] = self._MutableType( *self._original[b_index(self._original, key)] )
            return self.modified[key]
        except KeyError:
            self.added[key] = self._MutableType(key)
            return self.added[key]
    def __setitem__(self, key, value):
        self.__getitem__(key).copy(*value)
    def __delitem__(self, key):
        raise Exception("__delitem__ is not implemented")



Conversation = namedtuple('Conversation',['id','message_ids'])
class MutableConversation:
    def __init__(self, id, message_ids=None):
        self._id = id
        self._message_ids = [] if message_ids is None else message_ids
    @property
    def message_ids(self):
        if type(self._message_ids) is tuple:
            self._message_ids = list(self._message_ids)
        return self._message_ids
    def copy(self, *values):
        self._id, self._message_ids = values
    def __iter__(self):
        return (i for i in (self._id, tuple(self._message_ids)))
    def __repr__(self):
        return 'MutableConversation' + str((self._id, self._message_ids))



Message = namedtuple('Message',['id','flags','subject','sender','timestamp'])
class MutableMessage:
    def __init__(self, id, flags=None, subject=None, sender=None, timestamp=None):
        self._id = id
        self.flags = flags
        self.subject = subject
        self.sender = sender
        self.timestamp = timestamp
    def copy(self, *values):
        self._id, self.flags, self.subject, self.sender, self.timestamp = values
    def __iter__(self):
        return (i for i in (self._id, self.flags, self.subject, self.sender, self.timestamp))
    def __repr__(self):
        return 'MutableConversation' + str((self._id, self.flags, self.subject, self.sender, self.timestamp))
