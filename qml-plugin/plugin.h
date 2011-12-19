#ifndef MAILY_QML_PLUGIN_PLUGIN_H
#define MAILY_QML_PLUGIN_PLUGIN_H

#include <QtDeclarative/QDeclarativeExtensionPlugin>

class Qml_ComponentsPlugin : public QDeclarativeExtensionPlugin
{
    Q_OBJECT

public:
    void registerTypes(const char *uri);
};

#endif // MAILY_QML_PLUGIN_PLUGIN_H

