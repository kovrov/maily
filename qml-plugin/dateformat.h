#ifndef QML_COMPONENTS_DATEFORMAT_H
#define QML_COMPONENTS_DATEFORMAT_H

#include <QDeclarativeParserStatus>
#include <QMetaMethod>
#include <QDateTime>

class DateFormatCache;



class DateFormat : public QObject, public QDeclarativeParserStatus
{
    Q_OBJECT
    Q_INTERFACES (QDeclarativeParserStatus)
    Q_PROPERTY (DateFormatCache* cache READ getCache NOTIFY cacheChanged)

public:
    explicit DateFormat(QObject *parent = 0);
    virtual void classBegin() {} // do we need it?
    virtual void componentComplete();
    DateFormatCache* getCache() { return m_cache; }
    void format(QString &value, int &expires_in_secs, qint64 timestamp);

signals:
    void cacheChanged();

private:
    DateFormatCache *m_cache;
    QMetaMethod m_format;
};




class DateFormatCache : public QObject
{
    Q_OBJECT

public:
    explicit DateFormatCache(DateFormat *cache=0) : QObject(cache), m_dateFormat(cache) {}
    Q_INVOKABLE QString lookup(qint64 timestamp);

signals:
    void changed();

protected:
    void timerEvent(QTimerEvent *ev);

private:
    DateFormat *m_dateFormat;
    QHash<qint64, QString> m_hash;
    QDateTime m_expires;
};



#endif // QML_COMPONENTS_DATEFORMAT_H
