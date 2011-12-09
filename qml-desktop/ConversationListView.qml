import QtQuick 1.1


ListView {

    signal clicked(variant thrid)

    delegate: Item {
        id: listItem
        height: 80
        width: parent.width
        Row {
            anchors.fill: parent

            Column {
                width: parent.width
                anchors.verticalCenter: parent.verticalCenter

                Row {
                    width: parent.width
                    Text {
                        id: subjectText
                        text: model.subject
                        font.weight: Font.Bold
                        font.pixelSize: 26
                        width: countBubble.visible ? parent.width - countBubble.width : parent.width
                        elide: Text.ElideRight
                    }

                    Text {
                        id: countBubble
                        anchors.verticalCenter: parent.verticalCenter
                        text: model.count
                    }
                }

                Text {
                    id: timestampText
                    text: model.date
                    font.weight: Font.Light
                    font.pixelSize: 22
                    color: "#cc6633"
                    visible: text != ""
                    width: parent.width
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            onClicked: { listView.clicked(model.id) }
        }

        ListView.onAdd: ParallelAnimation {
            PropertyAction { target: listItem; property: "scale"; value: 0.75 }
            PropertyAction { target: listItem; property: "height"; value: 0 }
            NumberAnimation { target: listItem; property: "scale"; to: 1.0; duration: 75 }
            NumberAnimation { target: listItem; property: "height"; to: 88; duration: 75 }
        }
    }

    header: Component {
        id: listHeader
        Item {
            width: parent.width
            height: 0
            visible: listView.flickingVertically ? false : true
            opacity: listView.contentY > -32 ? 0 : (listView.contentY + 32) / -100;
            Text {
                text: "pull down to refresh"
                font.pointSize: 20
                anchors.bottom: parent.top
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottomMargin: 10
            }
        }
    }

    footer: Rectangle {
        id: moreButton
        signal clicked
        property alias text: getMore.text
        color: "darkGray"
        width: parent.width
        height: 48

        Text {
            id: getMore
            text: serviceAction.state == ServiceActionState.Undefined ? "get more" : "working..."
            font.pointSize: 20
            anchors.centerIn: parent
            color: "white"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {
                serviceAction.getMoreConversations(5)
            }
        }
        Rectangle {
            id: progressBar
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            height: 8
            width: parent.width * serviceAction.progress
            visible: serviceAction.state != ServiceActionState.Undefined
            color: "black"
        }
    }
}
