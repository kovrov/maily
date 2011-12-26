#!/usr/bin/python

import os.path
import platform
import sys
from PySide import QtCore as qt
from PySide.QtGui import  QApplication, QMainWindow
from PySide import QtDeclarative as qml
import imap
import store



class ConversationstModel(qt.QAbstractListModel):

    def __init__(self, store_mgr):
        qt.QAbstractListModel.__init__(self)
        self.setRoleNames(dict(enumerate(store.ConversationColumns)))
        self._sorted = store_mgr.snapshot.mailbox
        self._snapshot = store_mgr.snapshot
        store_mgr.conversationsChanged.connect(self.conversationsChanged)

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
        for begin, end in pairs(indices):
            self.beginInsertRows(qt.QModelIndex(), begin, end)
            self._sorted = self._sorted[:begin] + snapshot.mailbox[begin:end+1] + self._sorted[begin:]
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


on_device = platform.machine() == 'armv7l'
app = QApplication(sys.argv)

view = qml.QDeclarativeView()
view.setResizeMode(qml.QDeclarativeView.SizeRootObjectToView)

store_mgr = store.Store()
imap_client = imap.Client(store_mgr, 'xxx', 'yyy')
imap_client.start()  # Thread
service_action = imap.ServiceAction(imap_client)

try:
    model = ConversationstModel(store_mgr)

    ctx = view.rootContext()
    ctx.setContextProperty('pythonListModel', model)
    ctx.setContextProperty('ServiceActionState', dict(zip(imap.State._fields, imap.State)))
    ctx.setContextProperty('serviceAction', service_action)
    view.setSource(os.path.join(os.path.dirname(__file__),
                                'qml' if on_device else 'qml-desktop',
                                'main.qml'))
    window = QMainWindow()
    window.setCentralWidget(view)

    if on_device:
        window.showFullScreen()
    else:
        window.show()

    app.exec_()

finally:
    imap_client.call('terminate')
    imap_client.wait() #.join(0)
