#!/usr/bin/python

import sys
from PySide import QtCore as qt
from PySide.QtGui import  QApplication, QMainWindow
from PySide import QtDeclarative as qml
import imap
import store



class ConversationstModel(qt.QAbstractListModel):

    COLUMNS = ('self',)

    def __init__(self, store):
        qt.QAbstractListModel.__init__(self)
        self.setRoleNames(dict(enumerate(ConversationstModel.COLUMNS)))
        self._data = []
        store.conversationsChanged.connect(self.conversationsChanged)

    def rowCount(self, parent=qt.QModelIndex()):
        return len(self._data)

    def data(self, index, role):
        if index.isValid() and role == ConversationstModel.COLUMNS.index('self'):
            return self._data[index.row()]
        return None

    def conversationsChanged(self, snapshot, diff):
        modified, added = diff
        xxx = [store.b_index(snapshot.conversations, i) for i in added]
        pairs = zip([i for n,i in enumerate(xxx) if n == 0 or i - xxx[n-1] > 1],
                   [i+1 for n,i in enumerate(xxx) if n+1 == len(xxx) or xxx[n+1] - i > 1])

        for begin, end in pairs:
            self.beginInsertRows(qt.QModelIndex(), begin, end-1)
            for item in snapshot.conversations[begin:end]:
                self._data.append(Conversation(item))
            self.endInsertRows()



class Conversation(qt.QObject):

    def __init__(self, thread):
        qt.QObject.__init__(self)
        self.__id = str(thread[0])
        self.__senders = str(thread[1])

    changed = qt.Signal()
    subject = qt.Property(unicode, lambda self: self.__id, notify=changed)
    participants = qt.Property(unicode, lambda self: self.__senders, notify=changed)



class Controller(qt.QObject):

    def __init__(self):
        qt.QObject.__init__(self)
        self.store = store.Store()
        self.worker = imap.Client(self.store, 'xxx', 'yyy')
        self.worker.start()  # Thread

    def __del__(self):
        print "# join..."
        self.worker.join(0)  # Thread

    @qt.Slot(Conversation)
    def thingSelected(self, item):
        print 'User clicked on:', item



app = QApplication(sys.argv)

view = qml.QDeclarativeView()
view.setResizeMode(qml.QDeclarativeView.SizeRootObjectToView)

controller = Controller()
model = ConversationstModel(controller.store)

ctx = view.rootContext()
ctx.setContextProperty('controller', controller)
ctx.setContextProperty('pythonListModel', model)
view.setSource('desktop.qml')

button = view.rootObject().findChild(qt.QObject, "moreButton")
button.clicked.connect(lambda: controller.worker.call('getMoreConversations', 5))

window = QMainWindow()
window.setCentralWidget(view)
# window.showFullScreen()
window.show()

app.exec_()

controller.worker.call('terminate')
