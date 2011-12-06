import QtQuick 1.1


ListView {

    delegate: Item {
        id: listItem
        height: 88
        width: parent.width
        Row {
            anchors.fill: parent

            Column {
                width: parent.width
                anchors.verticalCenter: parent.verticalCenter

                Text {
                    id: subjectText
                    text: model.subject
                    font.weight: Font.Bold
                    font.pixelSize: 26
                    width: parent.width
                    elide: Text.ElideRight
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
            onClicked: {
                onClicked: { controller.thingSelected(model.id) }
            }
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
