var tigaMapCookie = 'tigaMapCookie';

function loadSavedLat() {
    var gotCookieString = getCookie(tigaMapCookie);
    var splitStr = gotCookieString.split("_");
    var savedMapLat = parseFloat(splitStr[0]);
    return savedMapLat;
}

function loadSavedLng() {
    var gotCookieString = getCookie(tigaMapCookie);
    var splitStr = gotCookieString.split("_");
    var savedMapLng = parseFloat(splitStr[1]);
    return savedMapLng;
}

function loadSavedZoom() {
    var gotCookieString = getCookie(tigaMapCookie);
    var splitStr = gotCookieString.split("_");
    var savedMapZoom = parseFloat(splitStr[2]);
    return savedMapZoom;
}


function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i<ca.length; i++) {
        var c = ca[i].trim();
        if (c.indexOf(name) == 0) return c.substring(name.length,c.length);
    }
    return "";
}


function saveMapState(map) {
    var mapZoom = map.getZoom();
    var mapCentre = map.getCenter();
    var mapLat = mapCentre.lat;
    var mapLng = mapCentre.lng;
    var cookiestring = mapLat + "_" + mapLng + "_" + mapZoom;
    var d = new Date();
    d.setTime(d.getTime() + (30 * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toGMTString();
    document.cookie = tigaMapCookie + "=" + cookiestring + ";expires=" + expires + ";domain=tigaserver.atrapaeltigre.com;path=/";
}


