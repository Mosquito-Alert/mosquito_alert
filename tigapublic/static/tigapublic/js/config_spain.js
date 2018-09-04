var MOSQUITO = (function (m, _) {
    m.config = _.extend(m.config || {}, {
        roles: {
            "notification": ['superexpert','gestors','notifier']
        },
        lngs: ['es', 'ca', 'en'],
        lngs_admin: ['es'],
        default_lng: ['es'],

        URL_API: '/tigapublic/',
        URL_PUBLIC: '/tigapublic/',
        
        lon: 1.130859375,
        lat: 37.53097889440026,
        maxzoom_cluster: 13,
        zoom: 5,
        login_allowed: true,
        embeded: window !== parent,
        minZoom: 1,

        default_layers: 'A',
        printreports:true,
        maxPrintReports: 300,
        "groups":[

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
                group:'none',
                title: 'layer.site',
                categories: {
                  'site_water': ['storm_drain_water'],
                  'site_dry': ['storm_drain_dry'],
                }
            },
            /*{
              'key': 'I',
              'group': 'none',
              'title': 'layer.predictionmodels',
              'deviation_min_zoom': 7,
              'prob_ranges': [
                  {'minValue':0, 'maxValue':0.25, 'color': 'rgba(255,255,178,0.5)', 'label': 'models.label.prob-1'},
                  {'minValue':0.25, 'maxValue':0.50, 'color': 'rgba(254,204,92,0.5)', 'label': 'models.label.prob-2'},
                  {'minValue':0.50, 'maxValue':0.75, 'color': 'rgba(253,141,60,0.5)', 'label': 'models.label.prob-3'},
                  {'minValue':0.75, 'maxValue':1, 'color': 'rgba(227,26,28,0.5)', 'label': 'models.label.prob-4'}
                ],
                'sd_ranges': [
                  {'minValue':0, 'maxValue':0.25, 'color': '#fff', 'label': 'models.label.sd-1'},
                  {'minValue':0.25, 'maxValue':0.5, 'color': '#c8b2b2', 'label': 'models.label.sd-2'},
                  {'minValue':0.50, 'maxValue':0.75, 'color': '#8f8c8c', 'label': 'models.label.sd-3'},
                  {'minValue':0.75, 'maxValue':1, 'color': '#000', 'label': 'models.label.sd-4'}
                ]
            },*/
            {
                key: 'F',
                group: 'none',
                title: 'layer.userfixes',
                'style': { // Default style for all items on this layer
                    //'color': 'red',
                    'color': 'green',
                    //'strokecolor': 'rgb(120,198,121)',
                    'strokecolor': 'rgb(120,198,121)',
                    'weight': 0.1,
                    'opacity': 0.8,
                    'fillColor': 'red',
                    'fillOpacity': 0.8
                },
                'segmentationkey': 'color', // name of the attribute that will be used to paint the different segments (color, opacity)
                'segments': [
                  {
                      "from": 0,
                      "to": 9,
                      "color": '65,171,93', // VERD
                      'opacity': 0.2 // only used when "segmentationkey" equals "opacity"
                    },{
                      "from": 10,
                      "to": 99,
                      "color": "35,132,67", //VERD
                      "opacity": 0.4
                    },{
                      "from": 100,
                      "to": 999,
                      "color": "0,104,55", //VERD
                      "opacity": 0.6
                    },{
                      "from": 1000,
                      "color": "0,69,41", //VERD
                      "opacity": 0.8
                    }
                ]
            }
        ],
        "logged": {
            "managers_group":['gestors'],
            "epidemiologist_group":['epidemiologist'],
            "lngs": ['es'],
            "groups":[
                {'name':'observations', 'icon': 'fa fa-mobile'},
                {'name': 'userdata', 'icon':'fa fa-user'},
                {'name': 'none', 'icon':''}
            ],
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
                  key: 'P',
                  group:'userdata',
                  title: 'layer.epidemiology',
                  default_palette:'patient_states',
                  palettes:{
                      'patient_states':{'name': 'patient_states',//select value
                                        'column': 'patient_state',
                                        'type':'qualitative',
                                        'images':{
                                                //Key vaues Witout accents
                                                'confirmat':'img/epi_confirmed.svg',
                                                'sospitos': 'img/epi_suspected.svg',
                                                'probable': 'img/epi_likely.svg',
                                                'indefinit': 'img/epi_none.svg',}
                      },
                      'patient_age':{'name': 'patient_age',//select value
                                    'column': 'age',
                                    'units': 'epidemiology.years',
                                    'type':'quantitative',
                                    'rangs':[
                                        {'name': '0-20', 'minValue':0, 'maxValue':20, 'image': 'img/epi_20.svg'},
                                        {'name': '21-35', 'minValue':21, 'maxValue':35, 'image': 'img/epi_35.svg'},
                                        {'name': '36-50', 'minValue':36, 'maxValue':50, 'image': 'img/epi_50.svg'},
                                        {'name': '51-65', 'minValue':51, 'maxValue':65, 'image': 'img/epi_65.svg'},
                                        {'name': '66...', 'minValue':66, 'maxValue':1000, 'image':'img/epi_66.svg'}
                                    ]
                      }
                  }

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
                'key': 'I',
                'group': 'none',
                'title': 'layer.predictionmodels',
                'deviation_min_zoom': 7,
                'prob_ranges': [
                  {'minValue':0, 'maxValue':0.25, 'color': 'rgba(255,255,178,0.5)', 'label': 'models.label.prob-1'},
                  {'minValue':0.25, 'maxValue':0.50, 'color': 'rgba(254,204,92,0.5)', 'label': 'models.label.prob-2'},
                  {'minValue':0.50, 'maxValue':0.75, 'color': 'rgba(253,141,60,0.5)', 'label': 'models.label.prob-3'},
                  {'minValue':0.75, 'maxValue':1, 'color': 'rgba(227,26,28,0.5)', 'label': 'models.label.prob-4'}
                ],
                'sd_ranges': [
                  {'minValue':0, 'maxValue':0.25, 'color': '#fff', 'label': 'models.label.sd-1'},
                  {'minValue':0.25, 'maxValue':0.5, 'color': '#c8b2b2', 'label': 'models.label.sd-2'},
                  {'minValue':0.50, 'maxValue':0.75, 'color': '#8f8c8c', 'label': 'models.label.sd-3'},
                  {'minValue':0.75, 'maxValue':1, 'color': '#000', 'label': 'models.label.sd-4'}
                ]
              },
              {
                  key: 'F',
                  group: 'none',
                  title: 'layer.userfixes',
                  'style': { // Default style for all items on this layer
                      'color': 'red',
                      'strokecolor': 'rgb(194,230,153)',
                      'weight': 0.1,
                      'opacity': 0.8,
                      'fillColor': 'red',
                      'fillOpacity': 0.8
                  },
                  'segmentationkey': 'color', // name of the attribute that will be used to paint the different segments (color, opacity)
                  'segments': [
                    {
                        "from": 0,
                        "to": 9,
                        "color": '65,171,93', // VERD
                        'opacity': 0.2 // only used when "segmentationkey" equals "opacity"
                      },{
                        "from": 10,
                        "to": 99,
                        "color": "35,132,67", //VERD
                        "opacity": 0.4
                      },{
                        "from": 100,
                        "to": 999,
                        "color": "0,104,55", //VERD
                        "opacity": 0.6
                      },{
                        "from": 1000,
                        "color": "0,69,41", //VERD
                        "opacity": 0.8
                      }
                  ]
              }
            ]
        }
    });

    return m;

}(MOSQUITO || {}, _));
