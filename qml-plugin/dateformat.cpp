#include <QString>
#include <QTimerEvent>
#include <QVariant>

#include "dateformat.h"



DateFormat::DateFormat(QObject *parent)
  : QObject (parent),
    m_cache (new DateFormatCache(this))
{
    connect(m_cache, SIGNAL(changed()), this, SIGNAL(cacheChanged()));
}


void DateFormat::componentComplete()
{
    const int method_idx = metaObject()->indexOfMethod("format(QVariant)");
    if (method_idx != -1) {
        m_format = metaObject()->method(method_idx);
    }
}



void DateFormat::format(QString &value, int &expires_in_secs, qint64 timestamp)
{
    expires_in_secs = -1;
    value = "invalid value";

    if (m_format.methodIndex() < 0) {
        value = QDateTime::fromMSecsSinceEpoch(timestamp).toString();
    }
    else {
        QVariant returnedValue;
        QVariant msg = timestamp;
        if (m_format.invoke(this, Qt::AutoConnection,
                            Q_RETURN_ARG(QVariant, returnedValue),
                            Q_ARG(QVariant, msg))) {

            if (QVariant::String == returnedValue.type()) {
                value = returnedValue.toString();
            }
            else if (QVariant::List == returnedValue.type()) {
                foreach (const QVariant &variant, returnedValue.toList()) {
                    if (QVariant::String == variant.type()) {
                        value = variant.toString();
                    }
                    else if (QVariant::Double == variant.type()) {
                        expires_in_secs = int(variant.toDouble());
                    }
                    else if (QVariant::Int == variant.type()) {
                        expires_in_secs = variant.toInt();
                    }
                }
            }
        }
    }
}



QString DateFormatCache::lookup(qint64 timestamp)
{
    QString &value = m_hash[timestamp];

    if (!value.isNull()) {
        return value;
    }

    int expires_in_secs;
    m_dateFormat->format(value, expires_in_secs, timestamp);

    if (expires_in_secs != -1) {
        const QDateTime now = QDateTime::currentDateTime();
        const QDateTime expires = now.addSecs(expires_in_secs);
        if (m_expires.isNull() || expires < m_expires) {
            m_expires = expires;
            startTimer(now.msecsTo(expires));
        }
    }

    return value;
}


void DateFormatCache::timerEvent(QTimerEvent *ev)
{
    killTimer(ev->timerId());
    m_hash.clear();
    m_expires = QDateTime();
    emit changed();
}
