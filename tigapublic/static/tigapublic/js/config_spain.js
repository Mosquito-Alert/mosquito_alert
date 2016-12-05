var MOSQUITO = (function (m, _) {
    m.config = _.extend(m.config || {}, {
        lngs: ['es', 'ca', 'en'],
        lngs_admin: ['es'],
        default_lng: ['es'],
        //URL_API: 'http://sigserver3.udg.edu/apps/mosquito/tigapublic/',
        //lon: 4.130859375,
        //lat: 38.53097889440026,
        lon: 1.130859375,
        lat: 37.53097889440026,
        zoom: 5,
        login_allowed: true,
        embeded: window !== parent,
        minZoom: 5,
        //lock_bounds: true,
        lock_bounds: {
          "ymin": 10.94304553343818,
          "ymax": 61.42951794712287,
          "xmin": -46.77148437499999,
          "xmax": 49.056640625
        },
        default_layers: 'A',
        printreports:true,
        maxPrintReports: 300,
        "layers": [
            {
                key: 'A',
                title: 'layer.tiger',
                categories: {
                  'albopictus_2': ['mosquito_tiger_probable', 'mosquito_tiger_confirmed']
                }
            },
            {
                key: 'B',
                title: 'layer.zika',
                categories: {
                  'aegypti_2': ['yellow_fever_probable', 'yellow_fever_confirmed']
                }
            },
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
                  'site_dry': ['storm_drain_dry'],
                }
            },
            {
                key: 'F',
                title: 'layer.userfixes',
                "style": { // Default style for all items on this layer
                    "color": "red",
                    "weight": 0.1,
                    "opacity": 0.8,
                    "fillColor": "red",
                    "fillOpacity": 0.8
                },
                "segmentationkey": 'color', // name of the attribute that will be used to paint the different segments
                "segments": [
                    {
                      "from": 0,
                      "to": 9,
                      "color": '#fdbb84', // only used when "segmentationkey" equals "color"
                      'opacity': 0.2 // only used when "segmentationkey" equals "opacity"
                    },{
                      "from": 10,
                      "to": 99,
                      "color": "#fc8d59",
                      "opacity": 0.4
                    },{
                      "from": 100,
                      "to": 999,
                      "color": "#e34a33",
                      "opacity": 0.6
                    },{
                      "from": 1000,
                      "color": "#b30000",
                      "opacity": 0.8
                    }
                ]
            }
        ],
        "logged": {
            "lngs": ['es'],
            "layers": [
              {
                  key: 'A2',
                  title: 'layer.mosquito_tiger_confirmed',
                  categories: {
                    'albopictus_2': ['mosquito_tiger_confirmed']
                  }
              },
              {
                  key: 'A1',
                  title: 'layer.mosquito_tiger_probable',
                  categories: {
                    'albopictus_1': ['mosquito_tiger_probable']
                  }
              },
              {
                  key: 'B2',
                  title: 'layer.yellow_fever_confirmed',
                  categories: {
                    'aegypti_2': ['yellow_fever_confirmed']
                  }
              },
              {
                  key: 'B1',
                  title: 'layer.yellow_fever_probable',
                  categories: {
                    'aegypti_1': ['yellow_fever_probable']
                  }
              },
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
                  key: 'G',
                  title: 'layer.unclassified',
                  categories: {
                    'unclassified': ['not_yet_validated']
                  },
                  private:true
              },
              {
                  key: 'E',
                  title: 'layer.site',
                  categories: {
                    'site_water': ['storm_drain_water'],
                    'site_dry': ['storm_drain_dry'],
                    'site_other': ['breeding_site_other'],
                    'site_pending': ['breeding_site_not_yet_filtered']
                  },
                  private:true
              },
              {
                  key: 'H',
                  title: 'layer.trash_layer',
                  categories: {
                    'trash': ['trash_layer']
                  },
                  private:true
              },
              {
                  key: 'F',
                  title: 'layer.userfixes',
                  "style": { // Default style for all items on this layer
                      "color": "red",
                      "weight": 0.1,
                      "opacity": 0.8,
                      "fillColor": "red",
                      "fillOpacity": 0.8
                  },
                  "segmentationkey": 'color', // name of the attribute that will be used to paint the different segments (color, opacity)
                  "segments": [
                      {
                        "from": 0,
                        "to": 9,
                        "color": '#fdbb84', // only used when "segmentationkey" equals "color"
                        'opacity': 0.2 // only used when "segmentationkey" equals "opacity"
                      },{
                        "from": 10,
                        "to": 99,
                        "color": "#fc8d59",
                        "opacity": 0.4
                      },{
                        "from": 100,
                        "to": 999,
                        "color": "#e34a33",
                        "opacity": 0.6
                      },{
                        "from": 1000,
                        "color": "#b30000",
                        "opacity": 0.8
                      }
                  ]
              }
            ]
        }
    });

    return m;

}(MOSQUITO || {}, _));
