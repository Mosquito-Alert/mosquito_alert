var MOSQUITO = (function (m, _) {
    m.config = _.extend(m.config || {}, {
        roles: {
            "notification": ['superexpert','gestors','notifier','supermosquito']
        },
        lngs: ['es', 'ca', 'en'],
        lngs_admin: ['es'],
        default_lng: ['es'],

        URL_API: '/tigapublic/',
        URL_PUBLIC: '/tigapublic/',
        URL_MODELS_VECTOR_GRID: '/static/tigapublic/models/vector/grid/', //TO DO: add it to static
        URL_MODELS_VECTOR_MUNICIPALITIES: '/static/tigapublic/models/vector/municipalities/',
        URL_MODELS_VIRUS_MUNICIPALITIES: '/static/tigapublic/models/virus/municipalities/',
        URL_MODELS_BITING: '/static/tigapublic/models/biting/',
        MODELS_FILE_NAME: 'mascp_monthly.csv',
        // BITING_FILE: 'mascp_monthly.csv',

        min_length_region_search: 4,
        show_bitting_sd: false,
        lon: 13.6889,
        lat: 44.8409,
        gridSize: 0.05,
        maxzoom_cluster: 13,
        zoom: 5,
        login_allowed: true,
        embeded: window !== parent,
        minZoom: 1,

        default_layers: 'A',
        printreports:true,
        maxPrintReports: 300,
        "groups":[
            {'name': 'observations', 'icon': 'fa fa-mobile'},
            {'name': 'models', 'icon':''},
            {'name': 'none', 'icon':''}
        ],
        deviation_min_zoom: 7,//Zoom when uncertainty first appears
        max_sd_radius: 100,//max size of uncertainty. In pixels
        keyLayersExcludedFromSharingURL:['M', 'N', 'R'],
        available_vectors_selector:[
            {'k': 'tig', 'v': 'layer.tiger'},
            //Uncomment to make them available on the select
            {'k': 'jap', 'v': 'layer.japonicus'}
            //{'k': 'yfv', 'v': 'layer.zike'},
        ],
        available_virus_selector:[
            {'k': 'den', 'v': 'layer.models.den'},
            //Uncomment to make them available on the select
            {'k': 'zk', 'v': 'layer.models.zika'},
            {'k': 'yf', 'v': 'layer.models.yf'},
            {'k': 'chk', 'v': 'layer.models.chk'},
            //{'k': 'wnv', 'v': 'layer.models.wnv'}
        ],
        ccaa: [
          {'k': '01', 'v': 'Andalucia'},
          {'k': '02', 'v': 'Aragon'},
          {'k': '03', 'v': 'Asturias'},
          {'k': '04', 'v': 'Baleares'},
          {'k': '05', 'v': 'Canarias'},
          {'k': '06', 'v': 'Cantabria'},
          {'k': '07', 'v': 'CastillaLeon'},
          {'k': '08', 'v': 'CastillaMancha'},
          {'k': '09', 'v': 'Cataluña'},
          {'k': '10', 'v': 'Valencia'},
          {'k': '11', 'v': 'Extremadura'},
          {'k': '12', 'v': 'Galicia'},
          {'k': '13', 'v': 'Madrid'},
          {'k': '14', 'v': 'Murcia'},
          {'k': '15', 'v': 'Navarra'},
          {'k': '16', 'v': 'PaisVasco'},
          {'k': '17', 'v': 'Rioja'},
          {'k': '18', 'v': 'Ceuta'},
          {'k': '19', 'v': 'Melilla'}
        ],
        months: ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                      'August', 'September', 'October', 'November', 'December'],
        "layers": [
            {
                key: 'A',
                group:'observations',
                subgroup:'none',
                title: 'layer.tiger',
                categories: {
                  'albopictus_2': ['mosquito_tiger_probable', 'mosquito_tiger_confirmed']
                }
            },
            {
                key: 'B',
                group:'observations',
                subgroup:'none',
                title: 'layer.zika',
                categories: {
                  'aegypti_2': ['yellow_fever_probable', 'yellow_fever_confirmed']
                }
            },
            {
                key: 'S',
                group:'observations',
                subgroup:'none',
                title: 'layer.japonicus',
                categories: {
                  'japonicus_2': ['japonicus_probable', 'japonicus_confirmed']
                }
            },
            {
                key: 'T',
                group:'observations',
                subgroup:'none',
                title: 'layer.koreicus',
                categories: {
                  'koreicus_2': ['koreicus_probable', 'koreicus_confirmed']
                }
            },
            {
                key: 'U',
                group:'observations',
                subgroup:'none',
                title: 'layer.culex',
                categories: {
                  'culex_2': ['culex_probable', 'culex_confirmed']
                }
            },
            {
                key: 'V',
                group:'observations',
                subgroup: 'combo',
                title: 'layer.jap_kor',
                categories: {
                  'jap_kor_2': ['japonicus_koreicus']
                }
            },
            {
                key: 'X',
                group:'observations',
                subgroup: 'combo',
                title: 'layer.mosquito_albo_cret',
                categories: {
                  'albo_cret': ['albopictus_cretinus']
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
                group:'observations',
                title: 'layer.site',
                categories: {
                  'site_water': ['storm_drain_water'],
                  'site_dry': ['storm_drain_dry'],
                  'site_other': ['breeding_site_other']
                }
            },

            //VECTOR (mosquito) models layer
            {
              'key': 'M',
              'group': 'models',
              'title': 'layer.predictionmodels.vector',
              'deviation_min_zoom': 7,
              // 'color_border_prob':'#bcbddc',
              'color_border_prob':'white',
              'color_border_sd':'black',
              'prob_ranges': [
                // {'minValue':-1, 'maxValue':-1, 'color': '#feebe2', 'label': 'models.label.prob-nodata'},
                {'minValue':0, 'maxValue':0.1, 'color': 'rgba(251,180,185,0.5)', 'label': 'models.label.prob-1'},
                {'minValue':0.1, 'maxValue':0.2, 'color': 'rgba(247,104,161,0.5)', 'label': 'models.label.prob-2'},
                {'minValue':0.2, 'maxValue':0.3, 'color': 'rgba(197,27,138,0.5)', 'label': 'models.label.prob-3'},
                {'minValue':0.3, 'maxValue':1, 'color': 'rgba(122,1,119,0.5)', 'label': 'models.label.prob-4'}
              ],
              'sd_ranges': [
                {'minValue':0, 'maxValue':0.05, 'color': '#fff', 'label': 'models.label.sd-1'},
                {'minValue':0.05, 'maxValue':0.1, 'color': '#c8b2b2', 'label': 'models.label.sd-2'},
                {'minValue':0.1, 'maxValue':0.15, 'color': '#8f8c8c', 'label': 'models.label.sd-3'},
                {'minValue':0.15, 'maxValue':1, 'color': '#000', 'label': 'models.label.sd-4'}
              ]
            },
            //BITING layer
            /*{
              'key': 'R',
              'group': 'models',
              'title': 'layer.biting',
              'deviation_min_zoom': 7,
              'color_border_prob':'orange',
              'color_border_sd':'black',
              'prob_ranges': [
                {'minValue':0, 'maxValue':0.1, 'color': 'rgba(254,237,222,0.5)', 'label': 'models.label.prob-1'},
                {'minValue':0.1, 'maxValue':0.2, 'color': 'rgba(253,190,133,0.5)', 'label': 'models.label.prob-2'},
                {'minValue':0.2, 'maxValue':0.3, 'color': 'rgba(253,141,60,0.5)', 'label': 'models.label.prob-3'},
                {'minValue':0.3, 'maxValue':1, 'color': 'rgba(217,71,1,0.5)', 'label': 'models.label.prob-4'}
              ],
              'sd_ranges': [
                {'minValue':0, 'maxValue':0.05, 'color': '#fff', 'label': 'models.label.sd-1'},
                {'minValue':0.05, 'maxValue':0.1, 'color': '#c8b2b2', 'label': 'models.label.sd-2'},
                {'minValue':0.1, 'maxValue':0.15, 'color': '#8f8c8c', 'label': 'models.label.sd-3'},
                {'minValue':0.15, 'maxValue':1, 'color': '#000', 'label': 'models.label.sd-4'}
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
                'color_border':'rgb(120,198,121)',
                'segmentationkey': 'color', // name of the attribute that will be used to paint the different segments (color, opacity)
                'segments': [
                    {
                      "from": 0, "to": 9,
                      "color": '65,171,93', 'opacity': 0.2
                    },{
                      "from": 10, "to": 99,
                      "color": "35,132,67", "opacity": 0.4
                    },{
                      "from": 100, "to": 999,
                      "color": "0,104,55", "opacity": 0.6
                    },{
                      "from": 1000,
                      "color": "0,69,41", "opacity": 0.8
                    }
                ]
            },
        ],
        "logged": {
            "managers_group":['gestors'],
            "superusers_group":['supermosquito'],
            "epidemiologist_edit_group":['epidemiologist'],
            "epidemiologist_view_group":['epidemiologist_viewer'],
            "lngs": ['es'],
            "groups":[
                {'name': 'observations', 'icon': 'fa fa-mobile'},
                {'name': 'userdata', 'icon':'fa fa-user'},
                {'name': 'models', 'icon':''},
                {'name': 'none', 'icon':''}
            ],
            "layers": [
              //VECTOR (mosquito) models
              {
                'key': 'M',
                'group': 'models',
                'title': 'layer.predictionmodels.vector',
                'deviation_min_zoom': 7,
                'color_border_prob':'white',
                'color_border_sd':'black',
                'prob_ranges': [
                  // {'minValue':-1, 'maxValue':-1, 'color': '#feebe2', 'label': 'models.label.prob-nodata'},
                  {'minValue':0, 'maxValue':0.1, 'color': 'rgba(251,180,185,0.5)', 'label': 'models.label.prob-1'},
                  {'minValue':0.1, 'maxValue':0.2, 'color': 'rgba(247,104,161,0.5)', 'label': 'models.label.prob-2'},
                  {'minValue':0.2, 'maxValue':0.3, 'color': 'rgba(197,27,138,0.5)', 'label': 'models.label.prob-3'},
                  {'minValue':0.3, 'maxValue':1, 'color': 'rgba(122,1,119,0.5)', 'label': 'models.label.prob-4'}
                ],
                'sd_ranges': [
                  {'minValue':0, 'maxValue':0.05, 'color': '#fff', 'label': 'models.label.sd-1'},
                  {'minValue':0.05, 'maxValue':0.1, 'color': '#c8b2b2', 'label': 'models.label.sd-2'},
                  {'minValue':0.1, 'maxValue':0.15, 'color': '#8f8c8c', 'label': 'models.label.sd-3'},
                  {'minValue':0.15, 'maxValue':1, 'color': '#000', 'label': 'models.label.sd-4'}
                ]
              },
              //VIRUS  models
              {
                'key': 'N',
                'group': 'models',
                'title': 'layer.predictionmodels.virus',
                'deviation_min_zoom': 7,
                'color_border_prob':'white',
                'color_border_sd':'black',
                'prob_ranges': [
                  // {'minValue':-1, 'maxValue':-1, 'color': 'rgba(255,2255,204,0.5)', 'label': 'models.label.prob-nodata'},
                  {'minValue':0, 'maxValue':0.1, 'color': 'rgba(161,218,180,0.5)', 'label': 'models.label.prob-1'},
                  {'minValue':0.1, 'maxValue':0.2, 'color': 'rgba(65,182,196,0.5)', 'label': 'models.label.prob-2'},
                  {'minValue':0.2, 'maxValue':0.3, 'color': 'rgba(44,127,184,0.5)', 'label': 'models.label.prob-3'},
                  {'minValue':0.3, 'maxValue':1, 'color': 'rgba(37,52,148,0.5)', 'label': 'models.label.prob-4'}
                ],
                'sd_ranges': [
                  {'minValue':0, 'maxValue':0.05, 'color': '#fff', 'label': 'models.label.sd-1'},
                  {'minValue':0.05, 'maxValue':0.1, 'color': '#c8b2b2', 'label': 'models.label.sd-2'},
                  {'minValue':0.1, 'maxValue':0.15, 'color': '#8f8c8c', 'label': 'models.label.sd-3'},
                  {'minValue':0.15, 'maxValue':1, 'color': '#000', 'label': 'models.label.sd-4'}
                ]
              },
              {
                  key: 'A2',
                  group:'observations',
                  subgroup:'tiger',
                  title: 'layer.mosquito_tiger_confirmed',
                  categories: {
                    'albopictus_2': ['mosquito_tiger_confirmed']
                  }
              },
              {
                  key: 'A1',
                  group:'observations',
                  subgroup:'tiger',
                  title: 'layer.mosquito_tiger_probable',
                  categories: {
                    'albopictus_1': ['mosquito_tiger_probable']
                  }
              },
              {
                  key: 'B2',
                  group:'observations',
                  subgroup:'zika',
                  title: 'layer.yellow_fever_confirmed',
                  categories: {
                    'aegypti_2': ['yellow_fever_confirmed']
                  }
              },
              {
                  key: 'B1',
                  group:'observations',
                  subgroup:'zika',
                  title: 'layer.yellow_fever_probable',
                  categories: {
                    'aegypti_1': ['yellow_fever_probable']
                  }
              },
              {
                  key: 'S2',
                  group:'observations',
                  subgroup:'japonicus',
                  title: 'layer.japonicus_confirmed',
                  categories: {
                    'japonicus_2': ['japonicus_confirmed']
                  }
              },
              {
                  key: 'S1',
                  group:'observations',
                  subgroup:'japonicus',
                  title: 'layer.japonicus_probable',
                  categories: {
                    'japonicus_1': ['japonicus_probable']
                  }
              },
              {
                  key: 'T2',
                  group:'observations',
                  subgroup:'koreicus',
                  title: 'layer.koreicus_confirmed',
                  categories: {
                    'koreicus_2': ['koreicus_confirmed']
                  }
              },
              {
                  key: 'T1',
                  group:'observations',
                  subgroup:'koreicus',
                  title: 'layer.koreicus_probable',
                  categories: {
                    'koreicus_1': ['koreicus_probable']
                  }
              },
              {
                  key: 'U2',
                  group:'observations',
                  subgroup:'culex',
                  title: 'layer.culex_confirmed',
                  categories: {
                    'culex_2': ['culex_confirmed']
                  }
              },
              {
                  key: 'U1',
                  group:'observations',
                  subgroup:'culex',
                  title: 'layer.culex_probable',
                  categories: {
                    'culex_1': ['culex_probable']
                  }
              },
              {
                  key: 'V',
                  group:'observations',
                  subgroup: 'combo',
                  title: 'layer.mosquito_jap_kor',
                  categories: {
                    'jap_kor': ['japonicus_koreicus']
                  }
              },
              {
                  key: 'X',
                  group:'observations',
                  subgroup: 'combo',
                  title: 'layer.mosquito_albo_cret',
                  categories: {
                    'albo_cret': ['albopictus_cretinus']
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
              //BITING layer
              /*{
                'key': 'R',
                'group': 'models',
                'title': 'layer.biting',
                'deviation_min_zoom': 7,
                'color_border_prob':'orange',
                'color_border_sd':'black',
                'prob_ranges': [
                  {'minValue':0, 'maxValue':0.1, 'color': 'rgba(254,237,222,0.5)', 'label': 'models.label.prob-1'},
                  {'minValue':0.1, 'maxValue':0.2, 'color': 'rgba(253,190,133,0.5)', 'label': 'models.label.prob-2'},
                  {'minValue':0.2, 'maxValue':0.3, 'color': 'rgba(253,141,60,0.5)', 'label': 'models.label.prob-3'},
                  {'minValue':0.3, 'maxValue':1, 'color': 'rgba(217,71,1,0.5)', 'label': 'models.label.prob-4'}
                ],
                'sd_ranges': [
                  {'minValue':0, 'maxValue':0.05, 'color': '#fff', 'label': 'models.label.sd-1'},
                  {'minValue':0.05, 'maxValue':0.1, 'color': '#c8b2b2', 'label': 'models.label.sd-2'},
                  {'minValue':0.1, 'maxValue':0.15, 'color': '#8f8c8c', 'label': 'models.label.sd-3'},
                  {'minValue':0.15, 'maxValue':1, 'color': '#000', 'label': 'models.label.sd-4'}
                ]
              },*/
              {
                  key: 'Q',
                  group: 'userdata',
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
                  categories: {
                    'state': ['suspected', 'confirmed']
                  },
                  default_palette: 'patient_states',
                  palettes:{
                      'patient_states':{
                          'name': 'patient_states',//select value
                          'column': 'patient_state',
                          'type':'qualitative',
                          'images':{
                              //Key vaues Witout accents
                              //This order will show on the epi layer legend
                              'confirmat_den': {'img':'img/epi_confirmed_den.svg', 'subgroup':'confirmat'},
                              'confirmat_wnv':{'img':'img/epi_confirmed_wnv.svg','subgroup': 'confirmat'},
                              'confirmat_yf':{'img':'img/epi_confirmed_yf.svg', 'subgroup': 'confirmat'},
                              'confirmat_zk':{'img':'img/epi_confirmed_zk.svg', 'subgroup': 'confirmat'},
                              'confirmat_chk':{'img':'img/epi_confirmed_chk.svg', 'subgroup': 'confirmat'},
                              'confirmat':{'img':'img/epi_confirmed_undefined.svg', 'subgroup': 'confirmat'},
                              'probable': {'img':'img/epi_likely.svg'},
                              'sospitos': {'img':'img/epi_suspected.svg'},
                              'no_cas': {'img':'img/epi_nocase.svg'},
                              'indefinit': {'img':'img/epi_none.svg'},
                          }
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
                  'color_border':'rgb(120,198,121)',
                  'segmentationkey': 'color', // name of the attribute that will be used to paint the different segments (color, opacity)
                  'segments': [
                    {
                      "from": 0, "to": 9,
                      "color": '65,171,93', 'opacity': 0.2
                    },{
                      "from": 10, "to": 99,
                      "color": "35,132,67", "opacity": 0.4
                    },{
                      "from": 100, "to": 999,
                      "color": "0,104,55", "opacity": 0.6
                    },{
                      "from": 1000,
                      "color": "0,69,41", "opacity": 0.8
                    }
                  ]
              }
            ]
        }
    });

    return m;

}(MOSQUITO || {}, _));
