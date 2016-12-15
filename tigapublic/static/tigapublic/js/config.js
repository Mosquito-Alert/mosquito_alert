var MOSQUITO = (function (m, _) {

    m.config = _.extend(m.config || {}, {
        lngs: ['en', 'es'],
        default_lng: 'en',
        //URL_API: 'http://127.0.0.1:8000/tigapublic/',
        URL_API: '/tigapublic/',
        //URL_PUBLIC: 'http://127.0.0.1:8000/tigapublic/',
        URL_PUBLIC: '/tigapublic/',
        //URL_API: '/apps/mosquito/tigapublic/',
        //URL_PUBLIC: 'http://0.0.0.0:8000/tigapublic/',
        //URL_PUBLIC: '/apps/mosquito/tigapublic/',
        showCoverageOnHover: true,
        lon: 11.25,
        lat: 35,
        zoom: 2,
        maxzoom_cluster: 15,
        login_allowed: false,
        embeded: window !== parent,
        default_layers: 'A,B',
        printreports:false,
        "layers": [
          {
              key: 'A',
              title: 'layer.tiger',
              //categories: ["albopictus#1#", "albopictus#2#"]
              categories: {
                'albopictus_2': ['mosquito_tiger_probable', 'mosquito_tiger_confirmed']
              }
          },
          {
              key: 'B',
              title: 'layer.zika',
              //categories: ["aegypti#1#", "aegypti#2#"]
              categories: {
                'aegypti_2': ['yellow_fever_confirmed', 'yellow_fever_probable']
              }
          }, //aegypti
          {
              key: 'C',
              title: 'layer.other_species',
              categories: {
                'noseparece': ['other_species']
              }
          },
          {
              key: 'D',
              title: 'layer.unidentified',
              categories: {
                'nosesabe': ['unidentified']
              }
          },
          {
              key: 'E',
              title: 'layer.site',
              categories: {
                'site_water': ['storm_drain_water'],
                'site_dry': ['storm_drain_dry']
              }
          }
      ],
      "logged": {
          "lngs": ['es'],
          "layers": []
      }
    });

    return m;

}(MOSQUITO || {}, _));
