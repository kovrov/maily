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
        self._data = store_mgr.snapshot.conversations
        store_mgr.conversationsChanged.connect(self.conversationsChanged)

    def rowCount(self, parent=qt.QModelIndex()):
        return len(self._data)

    def data(self, index, role):
        if not index.isValid():
            return None
        return self._data[index.row()][role]

    def conversationsChanged(self, snapshot, diff):
        modified_ids, added_ids = diff
        indices = [store.b_index(snapshot.conversations, i) for i in added_ids]
        pairs = zip([i for n,i in enumerate(indices) if n == 0 or i - indices[n-1] > 1],
                    [i for n,i in enumerate(indices) if n+1 == len(indices) or indices[n+1] - i > 1])
        for begin, end in pairs:
            self.beginInsertRows(qt.QModelIndex(), begin, end)
            self._data = self._data[:begin] + snapshot.conversations[begin:end+1] + self._data[begin:]
            self.endInsertRows()
        self._data = snapshot.conversations



class Controller(qt.QObject):

    def __init__(self):
        qt.QObject.__init__(self)
        self.store = store.Store()
        self.worker = imap.Client(self.store, 'xxx', 'yyy')
        self.worker.start()  # Thread

    def __del__(self):
        print "# join..."
        self.worker.join(0)  # Thread

    @qt.Slot(long)
    def thingSelected(self, item):
        print 'User clicked on:', item



on_device = platform.machine() == 'armv7l'
app = QApplication(sys.argv)

view = qml.QDeclarativeView()
view.setResizeMode(qml.QDeclarativeView.SizeRootObjectToView)

controller = Controller()
model = ConversationstModel(controller.store)

ctx = view.rootContext()
ctx.setContextProperty('controller', controller)
ctx.setContextProperty('pythonListModel', model)
view.setSource(os.path.join(os.path.dirname(__file__), 'main.qml' if on_device else 'desktop.qml'))

button = view.rootObject().findChild(qt.QObject, "moreButton")
button.clicked.connect(lambda: controller.worker.call('getMoreConversations', 5))

window = QMainWindow()
window.setCentralWidget(view)

if on_device:
    window.showFullScreen()
else:
    window.show()

app.exec_()

controller.worker.call('terminate')
