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
        self._by_date = store_mgr.snapshot.conversations_by_date
        self._snapshot = store_mgr.snapshot
        store_mgr.conversationsChanged.connect(self.conversationsChanged)

    def rowCount(self, parent=qt.QModelIndex()):
        return len(self._by_date)

    def data(self, index, role):
        if not index.isValid():
            return None
        date, uid = self._by_date[index.row()]
        i = store.b_index(self._snapshot.conversations, uid)
        return self._snapshot.conversations[i][role]

    def conversationsChanged(self, snapshot, diff):
        self._snapshot = snapshot
        modified_ids, added_ids = diff
        indices = [n for n,i in enumerate(snapshot.conversations_by_date) if i[1] in added_ids]
        pairs = zip([i for n,i in enumerate(indices) if n == 0 or i - indices[n-1] > 1],
                    [i for n,i in enumerate(indices) if n+1 == len(indices) or indices[n+1] - i > 1])
        for begin, end in pairs:
            self.beginInsertRows(qt.QModelIndex(), begin, end)
            self._by_date = self._by_date[:begin] + snapshot.conversations_by_date[begin:end+1] + self._by_date[begin:]
            self.endInsertRows()
        self._by_date = snapshot.conversations_by_date



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
