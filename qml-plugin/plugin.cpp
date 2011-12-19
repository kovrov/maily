#include "plugin.h"
#include "dateformat.h"

#include <QtDeclarative/qdeclarative.h>

void Qml_ComponentsPlugin::registerTypes(const char *uri)
{
    // @uri com.inc11.maily
    qmlRegisterType<DateFormat>(uri, 0, 1, "DateFormat");
    qmlRegisterType<DateFormatCache>(uri, 0, 1, "DateFormatCache");
}

Q_EXPORT_PLUGIN2(Qml_Components, Qml_ComponentsPlugin)

