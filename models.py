from PySide import QtCore as qt
import store


# workaround for http://bugs.pyside.org/show_bug.cgi?id=1113
_store = store.Store()

class ConversationsModel(qt.QAbstractListModel):

    def __init__(self, parent=None):
        super(ConversationsModel, self).__init__(parent)
        self.setRoleNames(dict(enumerate(store.ConversationColumns)))
        self._sorted = _store.snapshot.mailbox
        self._snapshot = _store.snapshot
        _store.conversationsChanged.connect(self.conversationsChanged)

    def rowCount(self, parent=qt.QModelIndex()):
        return len(self._sorted)

    def data(self, index, role):
        if not index.isValid():
            return None
        return self._snapshot.conversations[self._sorted[index.row()]][role]

    def conversationsChanged(self, snapshot, diff):
        self._snapshot = snapshot
        modified_ids, added_ids = diff
        indices = [n for n,i in enumerate(snapshot.mailbox) if snapshot.conversations[i].id in added_ids]
        for first, last in pairs(indices):
            self.beginInsertRows(qt.QModelIndex(), first, last)
            self._sorted = self._sorted[:first] + snapshot.mailbox[first:last+1] + self._sorted[first:]
            self.endInsertRows()
        self._sorted = snapshot.mailbox


def pairs(numbers):
    it = iter(numbers)
    x = y = next(it)
    for i in it:
        if i - y > 1:
            yield x, y
            x = i
        y = i
    yield x, y
