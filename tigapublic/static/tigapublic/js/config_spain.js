var MOSQUITO = (function (m, _) {
    m.config = _.extend(m.config || {}, {
        roles: {
            "notification": ['superexpert','gestors','notifier']
        },
        lngs: ['es', 'ca', 'en'],
        lngs_admin: ['es'],
        default_lng: ['es'],
        URL_API: '/tigapublic/',
        //URL_PUBLIC: 'http://sigserver3.udg.edu/apps/mosquito/tigapublic/',
        
        lon: 1.130859375,
        lat: 37.53097889440026,
        maxzoom_cluster: 13,
        zoom: 5,
        login_allowed: true,
        embeded: window !== parent,
        minZoom: 5,
        //lock_bounds: true,
        /*lock_bounds: {
          "ymin": 10.94304553343818,
          "ymax": 61.42951794712287,
          "xmin": -46.77148437499999,
          "xmax": 49.056640625
        },*/
        default_layers: 'A',
        printreports:true,
        maxPrintReports: 300,
        "groups":[
            //{'name':'observations', 'icon': 'fa fa-mobile'},
            //{'name':'breeding_sites', 'icon':'fa fa-dot-circle-o'},
            {'name': 'none', 'icon':''}
        ]
        ,
        "layers": [
            {
                key: 'A',
                group:'none',
                title: 'layer.tiger',
                categories: {
                  'albopictus_2': ['mosquito_tiger_probable', 'mosquito_tiger_confirmed']
                }
            },
            {
                key: 'B',
                group:'none',
                title: 'layer.zika',
                categories: {
                  'aegypti_2': ['yellow_fever_probable', 'yellow_fever_confirmed']
                }
            },
            {
                key: 'C',
                group:'none',
                title: 'layer.other_species',
                categories: {
                  'noseparece': ['other_species']
                }
            },
            {
                key: 'D',
                group:'none',
                title: 'layer.unidentified',
                categories: {
                  'nosesabe': ['unidentified']
                }
            },
            {
                key: 'E',
                //group:'breeding_sites',
                group:'none',
                title: 'layer.site',
                categories: {
                  'site_water': ['storm_drain_water'],
                  'site_dry': ['storm_drain_dry'],
                }
            },
            {
                key: 'F',
                group:'none',
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
                      "color": '253, 187, 132', // rgb
                      'opacity': 0.2 // only used when "segmentationkey" equals "opacity"
                    },{
                      "from": 10,
                      "to": 99,
                      "color": "252, 141, 89",
                      "opacity": 0.4
                    },{
                      "from": 100,
                      "to": 999,
                      "color": "227, 74, 51",
                      "opacity": 0.6
                    },{
                      "from": 1000,
                      "color": "179, 0, 0",
                      "opacity": 0.8
                    }
                ]
            }
        ],
        "logged": {
            "managers_group":['gestors'],
            "lngs": ['es'],
            "groups":[
                {'name':'observations', 'icon': 'fa fa-mobile'},
                //{'name': 'userfixes', 'icon':'fa fa-th-large'},
                {'name': 'userdata', 'icon':'fa fa-user'},
                //{'name':'observations', 'icon': 'fa fa-plus'},
                //{'name':'userdata', 'icon': 'fa fa-plus'},
                {'name': 'none', 'icon':''}
            ]
            ,
            "layers": [
              {
                  key: 'A2',
                  group:'observations',
                  title: 'layer.mosquito_tiger_confirmed',
                  categories: {
                    'albopictus_2': ['mosquito_tiger_confirmed']
                  }
              },
              {
                  key: 'A1',
                  group:'observations',
                  title: 'layer.mosquito_tiger_probable',
                  categories: {
                    'albopictus_1': ['mosquito_tiger_probable']
                  }
              },
              {
                  key: 'B2',
                  group:'observations',
                  title: 'layer.yellow_fever_confirmed',
                  categories: {
                    'aegypti_2': ['yellow_fever_confirmed']
                  }
              },
              {
                  key: 'B1',
                  group:'observations',
                  title: 'layer.yellow_fever_probable',
                  categories: {
                    'aegypti_1': ['yellow_fever_probable']
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
                  key: 'Q',
                  group:'userdata',
                  title: 'layer.drainstorm',
                  categories: {
                    'drainstorm': ['water', 'nowater']
                  },
                  radius:{'15':3, '17':4, '18':6, '19':8},//PAir values: zoom level, px size,
                  stroke: {'14':0, '19':1},
                  strokecolor: 'rgba(0,0,0,0.5)',
                  strokewidth: 1
              },
              {
                  key: 'G',
                  group:'observations',
                  title: 'layer.unclassified',
                  categories: {
                    'unclassified': ['not_yet_validated']
                  },
                  private:true
              },
              {
                  key: 'E',
                  title: 'layer.site',
                  group:'observations',
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
                  group:'observations',
                  title: 'layer.trash_layer',
                  categories: {
                    'trash': ['trash_layer']
                  },
                  private:true
              },
              {
                  key: 'F',
                  group: 'none',
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
                        "color": '253, 187, 132', // rgb
                        'opacity': 0.2 // only used when "segmentationkey" equals "opacity"
                      },{
                        "from": 10,
                        "to": 99,
                        "color": "252, 141, 89",
                        "opacity": 0.4
                      },{
                        "from": 100,
                        "to": 999,
                        "color": "227, 74, 51",
                        "opacity": 0.6
                      },{
                        "from": 1000,
                        "color": "179, 0, 0",
                        "opacity": 0.8
                      }
                  ]
              }
            ]
        }
    });

    return m;

}(MOSQUITO || {}, _));
