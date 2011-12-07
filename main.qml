import QtQuick 1.1
import com.nokia.meego 1.0



PageStackWindow
{
    id: rootWindow
    // showStatusBar: false
    // showToolBar: false
    property int pageMargin: UiConstants.DefaultMargin

    // ListPage is what we see when the app starts, it links to
    // the component specific pages
    initialPage: Page {
        id: pythonList
        anchors.margins: rootWindow.pageMargin
        orientationLock: PageOrientation.LockPortrait

        ConversationListView {
            id: listView
            anchors.fill: parent
            model: pythonListModel
        }

        ScrollDecorator { flickableItem: listView }
    }
}
