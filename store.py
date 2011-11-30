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
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if key < a[mid][0]:
            hi = mid
        else:
            lo = mid
        if key == a[lo][0]:
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
        self.__store = store
        self.__lock = Lock()
    def __enter__(self):
        self.__lock.acquire()
        return Transaction(self.__store)
    def __exit__(self, *args):
        self.__lock.release()


def merge(original, modified, added, Type):
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
        self.__store = store
        self.__snapshot = store.snapshot
        self.conversations = TransactionField(self.__snapshot.conversations, MutableConversation)
        self.messages = TransactionField(self.__snapshot.messages, MutableMessage)

    def addMessage(self, message_id, thread_id=None):
        if thread_id is not None:
            self.conversations[thread_id].message_ids.append(message_id)
            self.conversations[thread_id].message_ids.sort()
        self.messages[message_id].thread_id = thread_id

    def commit(self, block=True):
        new_conversations = merge(self.__snapshot.conversations, self.conversations.modified, self.conversations.added, Conversation)
        new_messages = merge(self.__snapshot.messages, self.messages.modified, self.messages.added, Message)
        self.__store.snapshot = Snapshot(conversations=new_conversations, messages=new_messages)
        self.__store.conversationsChanged.emit(self.__store.snapshot, (sorted(self.conversations.modified.keys()),
                                                                       sorted(self.conversations.added.keys())))



class TransactionField(object):
    def __init__(self, original, MutableType):
        self.__original = original
        self.__MutableType = MutableType
        self.added = {}
        self.modified = {}
        self.__removed = []
    def __getitem__(self, key):
        if key in self.added:
            return self.added[key]
        if key in self.modified:
            return self.modified[key]
        try:
            self.modified[key] = self.__MutableType( *self.__original[b_index(self.__original, key)] )
            return self.modified[key]
        except KeyError:
            self.added[key] = self.__MutableType(key)
            return self.added[key]
    def __setitem__(self, key, value):
        self.__getitem__(key).copy(*value)
    def __delitem__(self, key):
        raise Exception("__delitem__ is not implemented")



Conversation = namedtuple('Conversation',['id','message_ids'])
class MutableConversation:
    def __init__(self, id, message_ids=None):
        self.__id = id
        self.__message_ids = [] if message_ids is None else message_ids
    @property
    def message_ids(self):
        if type(self.__message_ids) is tuple:
            self.__message_ids = list(self.__message_ids)
        return self.__message_ids
    def copy(self, *values):
        self.__id, self.__message_ids = values
    def __iter__(self):
        return (i for i in (self.__id, tuple(self.__message_ids)))
    def __repr__(self):
        return 'MutableConversation' + str((self.__id, self.__message_ids))



Message = namedtuple('Message',['id','flags','subject','sender','timestamp'])
class MutableMessage:
    def __init__(self, id, flags=None, subject=None, sender=None, timestamp=None):
        self.__id = id
        self.flags = flags
        self.subject = subject
        self.sender = sender
        self.timestamp = timestamp
    def copy(self, *values):
        self.__id, self.flags, self.subject, self.sender, self.timestamp = values
    def __iter__(self):
        return (i for i in (self.__id, self.flags, self.subject, self.sender, self.timestamp))
    def __repr__(self):
        return 'MutableConversation' + str((self.__id, self.flags, self.subject, self.sender, self.timestamp))
