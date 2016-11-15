var MOSQUITO = (function (m, _) {

    m.config = _.extend(m.config || {}, {
        lngs: ['en', 'es'],
        default_lng: 'en',
        //URL_API: '/apps/mosquito/tigapublic/',
        URL_API: 'http://127.0.0.1:8000/tigapublic/',
        URL_PUBLIC: 'http://127.0.0.1:8000/tigapublic/',
        //URL_PUBLIC: '/apps/mosquito/tigapublic/',


        lon: 11.25,
        lat: 35,
        zoom: 2,
        maxzoom_cluster: 15,
        login_allowed: false
    });

    return m;

}(MOSQUITO || {}, _));
