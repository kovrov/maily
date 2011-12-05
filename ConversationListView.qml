import QtQuick 1.1


ListView {

    delegate: Item {
        id: listItem
        height: 88
        width: parent.width
        Row {
            anchors.fill: parent

            Column {
                anchors.verticalCenter: parent.verticalCenter

                Text {
                    id: subjectText
                    text: model.subject
                    font.weight: Font.Bold
                    font.pixelSize: 26
                }

                Text {
                    id: timestampText
                    text: model.date
                    font.weight: Font.Light
                    font.pixelSize: 22
                    color: "#cc6633"

                    visible: text != ""
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            onClicked: {
                onClicked: { controller.thingSelected(model.id) }
            }
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
            text: "get more"
            font.pointSize: 20
            anchors.centerIn: parent
            color: "white"
        }
        MouseArea {
            objectName: "moreButton"
            anchors.fill: parent
        }
    }
}
