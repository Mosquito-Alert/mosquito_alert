var MOSQUITO = (function (m, _) {

    m.config = _.extend(m.config || {}, {
        lngs: ['es', 'ca', 'en'],
        lngs_admin: ['es'],
        default_lng: ['es'],
        //URL_API: 'http://sigserver3.udg.edu/apps/mosquito_dades/',
        lon: 4.130859375,
        lat: 38.53097889440026,
        zoom: 5,
        login_allowed: true
    });

    return m;

}(MOSQUITO || {}, _));
