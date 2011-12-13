import QtQuick 1.1
import com.nokia.meego 1.0
import com.nokia.extras 1.1
import "format.js" as Format


ListView {

    signal clicked(variant thrid)

    delegate: Item {
        id: listItem
        height: UiConstants.ListItemHeightDefault
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
                        font: UiConstants.TitleFont
                        width: countBubble.visible ? parent.width - countBubble.width : parent.width
                        elide: Text.ElideRight
                    }

                    CountBubble {
                        id: countBubble
                        anchors.verticalCenter: parent.verticalCenter
                        value: model.count
                        visible: value != 1
                    }
                }

                Text {
                    id: timestampText
                    text: Format.elapsedTimestamp(model.date)
                    font: UiConstants.SubtitleFont
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
        height: UiConstants.ListItemHeightSmall

        Text {
            id: getMore
            text: serviceAction.state == ServiceActionState.InProgress ? "working..." : "get more"
            font.pointSize: 20
            anchors.centerIn: parent
            color: "white"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: { serviceAction.getMoreConversations(5) }
        }

        ProgressBar {
            id: progressBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            minimumValue: 0.0
            maximumValue: 1.0
            value: serviceAction.progress
            visible: serviceAction.state != ServiceActionState.Undefined
        }
    }
}
