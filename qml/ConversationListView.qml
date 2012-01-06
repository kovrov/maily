import QtQuick 1.1
import com.nokia.meego 1.0
import com.nokia.extras 1.1
import com.inc11.maily 0.1
import Maily 1.0


ListView {

    signal clicked(variant thrid)

    model: ConversationsModel {
    }

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
                    text: dateFormat.cache.lookup(model.date*1000)
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

    DateFormat {
        id: dateFormat

        /* if defined, function with this name will be called to get string
         * representation of date, and optionally expiration timer
         */
        function format(timestamp) {
            var date = new Date(timestamp)
            var now = new Date
            var minutes_ago = ((now - date) / 60000)<<0

            if (minutes_ago < 1) {
                return ["just now", 60]
            }

            if (minutes_ago < 60) {
                return [minutes_ago.toString() + " minutes ago", 60]
            }

            if (minutes_ago < 24*60) {
                return [((minutes_ago / 60)<<0).toString() + " hours ago",
                        (60 - (minutes_ago % 60)<<0) * 60]
            }

            if (minutes_ago < 30*24*60) {
                return [((minutes_ago / 60 / 24)<<0).toString() + " days ago",
                        (24*60 - (minutes_ago % (24*60))<<0) * 60]
            }

            return Qt.formatDate(date, Qt.DefaultLocaleLongDate)
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
        color: "darkGray"
        width: parent.width
        height: UiConstants.ListItemHeightSmall

        ServiceAction {
            id: serviceAction
            onStateChanged: {
                if (state == ServiceActionState.Failed) {
                    banner.text = "Aaaa!!!"
                    banner.show()
                }
            }
        }

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
