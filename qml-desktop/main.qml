import QtQuick 1.1



Item {
    ConversationListView {
        id: listView
        anchors.fill: parent
    }
    Rectangle {
        id: scrollbar
        anchors.right: listView.right
        y: listView.visibleArea.yPosition * listView.height
        width: 10
        height: listView.visibleArea.heightRatio * listView.height
        color: "black"
    }
}
