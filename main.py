#!/usr/bin/env python

import os.path
import platform
import sys
from PySide import QtCore as qt
from PySide.QtGui import  QApplication, QMainWindow
from PySide import QtDeclarative as qml
import imap
import models


on_device = platform.machine() == 'armv7l'
app = QApplication(sys.argv)

qml.qmlRegisterType(imap.ServiceAction, "Maily", 1, 0, "ServiceAction");
qml.qmlRegisterType(models.ConversationsModel, "Maily", 1, 0, "ConversationsModel");

view = qml.QDeclarativeView()
view.setResizeMode(qml.QDeclarativeView.SizeRootObjectToView)

ctx = view.rootContext()
ctx.setContextProperty('ServiceActionState', dict(zip(imap.State._fields, imap.State)))
ctx.engine().addImportPath('./qml-plugin')

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
