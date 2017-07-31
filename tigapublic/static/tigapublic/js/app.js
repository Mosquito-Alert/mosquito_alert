    (function (Backbone, $, MOSQUITO) {

    $.ajaxSetup({cache: false});

    var last_lang;

    var AppRouter = Backbone.Router.extend({

        initialize: function () {

            _.extend(this, Backbone.Events);

            ///
            this.route('/', 'map');
            //$zoom/$lat/$lon/
            this.route(/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/?$/, 'map');
            //$zoom/$lat/$lon/$layers/$year/$months
            this.route(/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/(.*)\/([\d,]*|all)\/([\d,]*|all)\/?$/, 'map');
            //this.route(/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/(([A-Z0-9],?)*)\/([\d]*|all)\/([\d,]*|all)\/?$/, 'map');

            //$zoom/$lat/$lon/$layers/$year/$months/$report
            //this.route(/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/([\d,]*)\/([\d-]*|all)\/([\d,]*|all)\/([\d]*)\/?$/, 'report');
            this.route(/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/(.*)\/([\d,]*|all)\/([\d,]*|all)\/([\d]*)\/?$/, 'report');

            //$lng/
            this.route(/([a-z]{2})\/?$/, 'map_i18n');

            //$lng/$zoom/$lat/$lon/
            this.route(/([a-z]{2})\/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/?$/, 'map_i18n');
            //$lng/$zoom/$lat/$lon/$layers/$year/$months
            //this.route(/([a-z]{2})\/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/([\d,]*)\/([\d]*|all)\/([\d,]*|all)\/?$/, 'map_i18n');
            this.route(/([a-z]{2})\/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/(.*)\/([\d,*]*|all)\/([\d,]*|all)\/?$/, 'map_i18n');


            this.route(/([a-z]{2})\/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/(.*)\/([\d,]*|all)\/([\d,]*|all)\/([\d]*)\/?$/, 'report_i18n');

            //Not registered users, no notifications param
            this.route(/reportsdocument\/(-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*)\/(.*)\/(.*)\/(.*)\/?$/, 'reportsdocument');
            this.route(/([a-z]{2})\/reportsdocument\/(-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*)\/(.*)\/(.*)\/(.*)\/?$/, 'reportsdocument_i18n');

            //Users, notifications param
            this.route(/reportsdocument\/(-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*)\/(.*)\/(.*)\/(.*)\/(.*)\/(.*)\/(.*)\/?$/, 'reportsdocument_notif');
            this.route(/([a-z]{2})\/reportsdocument\/(-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*)\/(.*)\/(.*)\/(.*)\/(.*)\/(.*)\/(.*)\/?$/, 'reportsdocument_notif_i18n');

            if(MOSQUITO.lng === undefined){
                MOSQUITO.lng = $('html').attr('lang');
            }

            trans.on('i18n_lang_changed', function(lng){
                MOSQUITO.lng = lng;
            });


        },

        routes: {
            '': 'map'
        },

        map: function(zoom, lat, lon, layers, years, months) {
            this.map_i18n(MOSQUITO.config.default_lng, zoom, lat, lon, layers, years, months);
        },

        map_i18n: function(lng, zoom, lat, lon, layers, years, months) {
            console.log('map')
            if($('#page-map').is(':hidden')){
                $('.page').hide();
                $('#page-map').show();
            }
            var options = {};

            //_.extend(trans.ca, add);
            if(zoom !== undefined && lat !== undefined && lon !== undefined){
                options.zoom = zoom;
                options.lat = lat;
                options.lon = lon;
            }

            if(!this.headerView){
                this.headerView = new HeaderView();
            }
            // Particular case. Enter spain.html but already logged
            if(layers === undefined || layers === null || layers.length === 0){
                if (('mapView' in MOSQUITO.app) && ('options' in MOSQUITO.app.mapView)) {
                  layers = MOSQUITO.app.mapView.options.layers.join(',');
                } else {
                  layers = MOSQUITO.config.default_layers;
                }
            }
            else{
                if (layers==='all'){
                    layers = this.getAllLayersFromConf();
                }
            }
            options.layers = this.getSelectedLayersFromURL(layers);

            if(years !== undefined && years !== 'all'){
                options.filters_years = years;
            }

            if(months !== undefined && months !== 'all'){
                options.filters_months = months;
            }

            if(!this.mapView){
                this.mapView = new MapView(options);
            }else{
                //console.debug('TODO: Cal aplicar noves condicions');
                this.mapView.redraw(options);
            }

            // IS EMBEDED?
            if (!MOSQUITO.config.embeded) this.addCookieConsent();
            else {
              MOSQUITO.app.headerView.remove();
              MOSQUITO.app.mapView.$el.css('top',0);
              map.scrollWheelZoom.disable();
            }

            if(lng !== last_lang){
                t().change(lng);
            }
            last_lang = lng;
        },

        report: function(lng, zoom, lat, lon, layers, years, months, report_id){
            this.report_i18n(MOSQUITO.config.default_lng, lng, zoom, lat, lon, layers, years, months, report_id);
        },

        report_i18n: function(lng, zoom, lat, lon, layers, years, months, report_id){
            //MOSQUITO.config.clusterize = false;
            var _this = this;
            var show_report;
            show_report = function(){

                _this.mapView.scope.report_id = report_id;
                var found = _.find(_this.mapView.layers.layers.mcg.getLayers(), function(layer){
                    if(layer._data.id === parseInt(report_id) &&
                        _this.mapView.map.hasLayer(layer)
                    ){
                        return layer;
                    }
                });

                if(found !== undefined){
                    var icon  = $(found._icon);
                    var p = icon.offset();
                    var w = icon.width();
                    found.fire('click',
                        {
                            layer: found,
                            latlng:[lat,lon],
                            originalEvent: {
                                pageX: p.left + w/2,
                                pageY: p.top
                            }
                        }
                    );
                }
                else{
                    //search inside clusters
                    var cluster = _.find(_this.mapView.layers.layers.mcg._featureGroup._layers, function(layer){
                        if ( '_group' in layer){
                            // search marker inside clusters
                            var marker = _.find(layer._markers, function(m){
                                if ( m._data.id === parseInt(report_id) ) {
                                    return m;
                                }
                            })
                            if(marker !== undefined){
                                layer.spiderfy();
                                marker.fireEvent('click',{latlng:[0,0]});//latlng required for fireEvent
                                //return layer;
                            }
                        }
                    })
                    //}
                }
                this.off('cluster_drawn', show_report);
            };

            this.map_i18n(lng, zoom, lat, lon, layers, years, months);
            this.on('cluster_drawn', show_report);


        },

        reportsdocument: function(bbox, years, months, categories){
            this.reportsdocument_i18n(MOSQUITO.config.default_lng, bbox, years, months, categories);
        },

        reportsdocument_i18n: function(lng, bbox, years, months, categories){
            $('.page').hide();
            $('#page-reports').show();
            MOSQUITO.lng = lng;
            new ReportsdocumentView({bbox: bbox, years: years, months:months, categories: categories});
            //window.location.hash = '#/' + last_lang;
        },

        reportsdocument_notif: function(bbox, years, months, categories, notifications, hashtag, notif_types){
            console.log('reports document notif');
            this.reportsdocument_notif_i18n(MOSQUITO.config.default_lng, bbox, years, months, categories, notifications, hashtag, notif_types);
        },

        reportsdocument_notif_i18n: function(lng, bbox, years, months, categories, notifications, hashtag, notif_types){
          console.log(hashtag)
            $('.page').hide();
            $('#page-reports').show();
            MOSQUITO.lng = lng;
            new ReportsdocumentView({bbox: bbox, years: years, months:months, categories: categories, notifications: notifications, hashtag:hashtag, notif_types: notif_types});
            //window.location.hash = '#/' + last_lang;
        },

        addCookieConsent: function() {
          cook = document.cookie;
          if ($('#cookie_consent').length>0 || cook.indexOf('cookie_consent_accepted=TRUE') > -1) {
            //document.cookie = "cookie_consent_accepted=FALSE; expires=Thu, 01 Jan 1970 00:00:00 UTC";
          } else {
            container = $('<div></div>')
              .addClass('cookie_consent')
              .attr('id', 'cookie_consent')
              .css('width', '100%');
              //.css('top', $('#header-view').height());
            maintext = $('<p></p>').attr('i18n', 'map.cookie_consent');
            container.append(maintext);
            accepttext = $('<button></button>').attr('i18n', 'map.cookie_accept');
            accepttext.on('click', function(e) {
              e.stopPropagation();
              e.preventDefault();
              $('#cookie_consent').slideUp();
              document.cookie = "cookie_consent_accepted=TRUE";
            })
            container.append(accepttext);
            $('#map').append(container);
          }
      },

      getAllLayersFromConf: function (){
          var layers=[], user_layers=[];
          if (MOSQUITO.app.headerView.logged){
              var user_layers = MOSQUITO.config.logged.layers;
          }
          else{
              var user_layers = MOSQUITO.config.layers;
          }

          for (var i = 0; i < user_layers.length; i++){
              if (user_layers[i].key === 'F') continue; //do not consider userfixes
              layers.push(user_layers[i].key);
          }
          return layers.join(',');
      },

      //translate layers identifiers to layers array position
      getSelectedLayersFromURL: function (layers){
          var ar =[];
          var layersArray = layers.split(',');
          if (MOSQUITO.app.headerView.logged) {
              var user_layers = MOSQUITO.config.logged.layers;
              for (var l=0 ; l < user_layers.length ; l++ ){
                  for (var j=0; j < layersArray.length; j++){
                      //From general to detailed
                      if (user_layers[l].key.indexOf(layersArray[j])!==-1) {
                          if (ar.indexOf(user_layers[l].key) === -1){ //avoid duplicate values
                              ar.push(user_layers[l].key);
                          }
                      }
                      else{ //check inside categories
                        for (var k in user_layers[l].categories) {
                          for (var h=0; h < user_layers[l].categories[k].length; h++) {
                            if (user_layers[l].categories[k][h].indexOf(layersArray[j])!==-1)
                              ar.push(user_layers[l].key);
                          }
                        }
                      }
                  }
              }

          }
          else{
              var user_layers = MOSQUITO.config.layers;
              for (var j=0; j < layersArray.length; j++){
                  for (var l=0 ; l < user_layers.length ; l++ ){
                      //From detailed to general
                      if (layersArray[j].indexOf(user_layers[l].key)!==-1) {
                          if (ar.indexOf(user_layers[l].key) === -1){ //avoid duplicate values
                              ar.push(user_layers[l].key);
                          }
                      }
                      else{ //check inside categories
                        for (var k in user_layers[l].categories) {
                          for (var h=0; h < user_layers[l].categories[k].length; h++) {
                            if (user_layers[l].categories[k][h].indexOf(layersArray[j])!==-1){
                              ar.push(user_layers[l].key);
                            }
                          }
                        }
                      }
                  }
              }
          }

          return ar.join(',');
      }

    });

    MOSQUITO.app = new AppRouter();
    Backbone.history.start();



}(Backbone, jQuery, MOSQUITO || {}));
