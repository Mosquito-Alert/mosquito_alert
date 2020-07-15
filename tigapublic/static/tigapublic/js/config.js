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
        autocomplete_min_chars: 2,
        calendar_presets: [
          {
             text: 'general.today',
             dateStart: function() { return moment() },
             dateEnd: function() { return moment()}
          },
          {
             text: 'general.yesterday',
             dateStart: function() { return moment().subtract(1, 'days') },
             dateEnd: function() { return moment().subtract(1, 'days') }
          },
          {
             text: 'general.before_yesterday',
             dateStart: function() { return moment().subtract(2, 'days') },
             dateEnd: function() { return moment().subtract(2, 'days') }
          },
          {
             text: 'group.filters.shortcut.this_week',
             dateStart: function() { return moment().startOf('isoweek') },
             dateEnd: function() { return moment() }
          },
          {
             text: 'group.filters.shortcut.last_7_days',
             dateStart: function() { return moment().subtract(1, 'week') },
             dateEnd: function() { return moment() }
          }
        ],
        "groups":[
            {'name':'observations', 'icon': 'fa fa-mobile'},
        ],
        "layers": [
          {
              key: 'A',
              group:'observations',
              title: 'layer.tiger',
              //categories: ["albopictus#1#", "albopictus#2#"]
              categories: {
                'albopictus_2': ['mosquito_tiger_probable', 'mosquito_tiger_confirmed']
              }
          },
          {
              key: 'B',
              group:'observations',
              title: 'layer.zika',
              //categories: ["aegypti#1#", "aegypti#2#"]
              categories: {
                'aegypti_2': ['yellow_fever_confirmed', 'yellow_fever_probable']
              }
          }, //aegypti
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
