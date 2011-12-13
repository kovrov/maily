
var cache = {}
var cache_timer = Qt.createQmlObject('import QtQuick 1.1; Timer { repeat: false }', Qt.application)
var cache_expire = null

function onTimer(timestamp) {
    cache = {}
    cache_expire = null
}

cache_timer.triggered.connect(onTimer)

function elapsedTimestamp(timestamp) {
    if (timestamp in cache) {
        return cache[timestamp]
    }

    var date = new Date(timestamp*1000)
    var now = new Date
    var minutes_ago = ((now - date) / 60000)<<0
    var expires = null

    if (minutes_ago < 1) {
        cache[timestamp] = "just now"
        expires = new Date(now.getTime() + 60*1000)
    }
    else if (minutes_ago < 60) {
        cache[timestamp] = minutes_ago.toString() + " minutes ago"
        expires = new Date(now.getTime() + 60*1000)
    }
    else if (minutes_ago < 24*60) {
        cache[timestamp] = ((minutes_ago / 60)<<0).toString() + " hours ago"
        expires = new Date(now.getTime() + (60 - (minutes_ago % 60)<<0) * 60*1000)
    }
    else if (minutes_ago < 30*24*60) {
        cache[timestamp] = ((minutes_ago / 60 / 24)<<0).toString() + " days ago"
        expires = new Date(now.getTime() + (24*60 - (minutes_ago % (24*60))<<0) * 60*1000)
    }
    else {
        cache[timestamp] = Qt.formatDate(date, Qt.DefaultLocaleLongDate)
        // cache[timestamp] = Qt.formatDate(date, Qt.TextDate)
    }

    if (null != expires && (null == cache_expire || expires < cache_expire)) {
        cache_expire = expires
        cache_timer.interval = expires - now
        cache_timer.restart()
    }

    return cache[timestamp]
}
