var MOSQUITO = (function (m, _) {

    m.config = _.extend(m.config || {}, {
        lngs: ['en', 'es'],
        default_lng: 'en',
        URL_API: '/tigapublic/',
        URL_PUBLIC: '/tigapublic/',
        showCoverageOnHover: true,
        lon: 11.25,
        lat: 35,
        zoom: 2,
        maxzoom_cluster: 20,
        login_allowed: false,
        embeded: window !== parent,
        default_layers: 'A,B',
        printreports:false,
        "groups":[
            {'name':'observations', 'icon': 'fa fa-mobile'},
        ],
        "layers": [
          {
              key: 'A',
              group:'observations',
              title: 'layer.tiger',
              categories: {
                'albopictus_2': ['mosquito_tiger_probable', 'mosquito_tiger_confirmed']
              }
          },
          {
              key: 'B',
              group:'observations',
              title: 'layer.zika',
              categories: {
                'aegypti_2': ['yellow_fever_confirmed', 'yellow_fever_probable']
              }
          }, 
          {
              key: 'C',
              group:'observations',
              title: 'layer.other_species',
              categories: {
                'noseparece': ['other_species']
              }
          },
          {
              key: 'D',
              group:'observations',
              title: 'layer.unidentified',
              categories: {
                'nosesabe': ['unidentified']
              }
          },
          {
              key: 'E',
              title: 'layer.site',
              group:'observations',
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
