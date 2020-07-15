(function (Backbone, $, MOSQUITO) {

$.ajaxSetup({cache: false});

var last_lang;
var AppRouter = Backbone.Router.extend({

    initialize: function () {

        _.extend(this, Backbone.Events);
        //Regular expressions for each possible param

        var re_lang = new RegExp(/^([a-z]{2})\/?/i).source
        var re_zoom = new RegExp(/\/?(\d{1,2})\/?/i).source
        var re_lat = new RegExp(/\/([-\d\.,]+)\/?/i).source
        var re_lon = re_lat
        var re_layers = new RegExp(/\/([^ /]+)\/?/i).source
        var re_years = new RegExp(/\/([\d,]+|all)\/?/i).source
        var re_months = new RegExp(/\/([\d,]+|all)\/?/i).source
        var re_hashtag = new RegExp(/\/([^ /]+)\/?/i).source
        var re_munis = new RegExp(/\/([N,0-9]+)\/?/i).source
        var re_report = new RegExp(/\/(\d+)\/?/i).source
        var re_bbox = new RegExp(/([-\d\.,]*)\/?/i).source
        var re_notif = new RegExp(/([^ /]+)\/?/i).source
        var re_notiftype = new RegExp(/([^ /]+)\/?/i).source
        //day-month-year
        var re_startdate = new RegExp(/(\d{4}-\d{1,2}-\d{1,2})\/?/i).source
        var re_enddate = re_startdate
        var re_end = new RegExp('\/?$').source;

        var re =  new RegExp(
            re_end
        );
        this.route(re, 'map');

        var re = new RegExp(re_lang + re_end )
        //lang
        this.route(re, 'map_i18n');

        var re =  new RegExp(
            re_lang + re_zoom + re_lat + re_lon + re_end
        );
        //$lng/$zoom/$lat/$lon/
          this.route(re, 'map_i18n');

        var re = new RegExp(
          re_lang + re_zoom + re_lat + re_lon + re_layers + re_startdate +
          re_enddate + re_hashtag + re_munis + re_end
        )

        //$lng/$zoom/$lat/$lon/$layers/$dateStart/$dateEnd/hashtag
        this.route(re, 'map_daterange');


        var re = new RegExp(
          re_lang + re_zoom + re_lat + re_lon + re_layers + re_years +
          re_months + re_hashtag + re_munis + re_end
        )
        //$lng/$zoom/$lat/$lon/$layers/$year/$months/hashtag/municipalities
        this.route(re, 'map_no_daterange');

        var re = new RegExp(
          re_lang + re_zoom + re_lat + re_lon + re_layers + re_years +
          re_months + re_hashtag + re_munis + re_report + re_end
        )

        //lang, zoom, lat, lon, layers, years, months, hashtag, munis, report
        this.route(re, 'report_no_daterange');

        var re = new RegExp(
          re_lang + re_zoom + re_lat + re_lon + re_layers + re_startdate +
          re_enddate + re_hashtag + re_munis + re_report + re_end
        )
        //lang, zoom, lat, lon, layers, startDate, endDate, hashtag, munis, report
        this.route(re, 'report_daterange');

        var re = new RegExp(
          re_lang + '\/reportsdocument\/?' + re_bbox + re_startdate + re_enddate +
          re_layers + re_hashtag + re_munis + re_end
        )
        //PUBLIC, bbox,years,months,layers,hashtag,munis
        this.route(re, 'reportsdocument_public_daterange');


        var re = new RegExp(
          re_lang + '\/reportsdocument\/?' + re_bbox + re_years + re_months +
          re_layers + re_hashtag + re_munis + re_end
        )
        //PUBLIC, lng,bbox,years,months,layers,hashtag, munis
        this.route(re, 'reportsdocument_public_no_daterange');

        var re = new RegExp(
          re_lang + '\/reportsdocument\/?' + re_bbox + re_years + re_months
          + re_layers + re_hashtag + re_munis + re_notif + re_notiftype + re_end
        )
        //PRIVATE bbox,years,months,layers,hashtag,munis,
        //mynotifications,notificationstype
        this.route(re, 'reportsdocument_private_no_daterange');

        var re = new RegExp(
          re_lang + '\/reportsdocument\/?' + re_bbox + re_startdate + re_enddate
          + re_layers + re_hashtag + re_munis + re_notif + re_notiftype + re_end
        )
        //PRIVATE bbox,years,months,layers,hashtag,munis,
        //mynotifications,notificationstype
        this.route(re, 'reportsdocument_private_daterange');

        var re = new RegExp(
          re_lang + '\/reportsdocument\/?' + re_bbox + re_years + re_months +
          re_layers + re_hashtag + re_munis +
          re_notif + re_notiftype + re_end
        )
        //PRIVATE lng,bbox,years,months,layers,hashtag,munis
        //mynotifications,notificationstype
        this.route(re, 'reportsdocument_private_no_daterange');

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
        var empty_hashtag = 'N'
        var empty_municipalities = 'N'
        this.map_i18n(MOSQUITO.config.default_lng, zoom, lat, lon, layers, years, months, false, false, empty_hashtag, empty_municipalities);
    },

    map_daterange: function(lng, zoom, lat, lon, layers, startDate, endDate, hashtag, munis) {
        this.map_i18n(lng, zoom, lat, lon, layers, 'all', 'all', startDate, endDate, hashtag, munis);
    },

    map_no_daterange: function(lng, zoom, lat, lon, layers, years, months, hashtag, munis) {
        this.map_i18n(lng, zoom, lat, lon, layers, years, months, false, false, hashtag, munis);
    },

    map_i18n: function(lng, zoom, lat, lon, layers, years, months, dateStart, dateEnd, hashtag, munis) {
        //Initialize  params if necessary
        if (lng===undefined) lng = MOSQUITO.config.default_lng;
        if (zoom===undefined) zoom = MOSQUITO.config.zoom;
        if (lat===undefined) lat = MOSQUITO.config.lat;
        if (lon===undefined) lon = MOSQUITO.config.lon;
        if (years===undefined) years='all';
        if (months===undefined) months='all';
        if (layers===undefined) layers = MOSQUITO.config.default_layers;
        if (hashtag===undefined) hashtag='N';
        if (munis === undefined) munis= 'N';
        if (dateStart === undefined) dateStart= false;
        if (dateEnd === undefined) dateEnd= false;

        if (dateStart) dateStart = moment(dateStart, 'YYYY-MM-DD').toDate();
        if (dateEnd) dateEnd = moment(dateEnd, 'YYYY-MM-DD').toDate();

        if($('#page-map').is(':hidden')){
            $('.page').hide();
            $('#page-map').show();
        }
        var options = {};
        options.zoom = zoom;
        options.lat = lat;
        options.lon = lon;

        if(!this.headerView){
            this.headerView = new HeaderView();
        }

        // Particular case. Enter spain.html but already logged
        if(layers === null || layers.length === 0){
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

        if(years !== 'all'){
            options.filters_years = years;
        }

        if(months !== 'all'){
            options.filters_months = months;
        }

        if (dateStart && dateEnd) {
          options.filters_daterange = {'start': dateStart, 'end': dateEnd};
        }

        if(hashtag !== 'N'){
            options.filters_hashtag = hashtag;
        }else{
          options.filters_hashtag = 'N';
        }

        if( munis !== 'N' && munis !== '0' ){
            options.filters_municipalities = munis.split(',');
        }else{
          options.filters_municipalities = munis
        }

        //Keep drawing map after loggin response from ajax
        var drawMapAfterLoggin = function(e){
          //get layers based on logged status
          options.layers = this.getSelectedLayersFromURL(layers);
          if(!this.mapView){
              this.mapView = new MapView(options);
          }else{
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
        }

        MOSQUITO.app.once('app_logged', drawMapAfterLoggin);

        if (this.mapView){
          if(lng !== last_lang){
              t().change(lng);
          }
          last_lang = lng;
        }
    },

    report: function(lng, zoom, lat, lon, layers, years, months, hashtag, munis, report_id){
      this.report_i18n(MOSQUITO.config.default_lng, lng, zoom, lat, lon, layers, years, months, false, false, hashtag, munis, report_id);
    },

    report_daterange: function(lng, zoom, lat, lon, layers, startDate, endDate, hashtag, munis, report_id){
      this.report_i18n(lng, zoom, lat, lon, layers, 'all', 'all', startDate, endDate, hashtag, munis, report_id);
    },

    report_no_daterange: function(lng, zoom, lat, lon, layers, years, months, hashtag, munis, report_id){
      this.report_i18n(lng, zoom, lat, lon, layers, years, months, false, false, hashtag, munis, report_id);
    },

    report_i18n: function(lng, zoom, lat, lon, layers, years, months, startDate, endDate, hashtag, munis, report_id){
        //MOSQUITO.config.clusterize = false;
        var _this = this;
        var show_report;

        this.map_i18n(lng, zoom, lat, lon, layers, years, months, startDate, endDate, hashtag, munis);
        //After check login keep showing report
        MOSQUITO.app.on('app_logged', function(e){
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
              }
              this.off('cluster_drawn', show_report);
          };
          this.on('cluster_drawn', show_report);
        });

    },

    //REPORT DOCUMENTS FOR PUBLIC USERS
    reportsdocument_public_no_daterange: function(lng, bbox, years, months, categories, hashtag, munis) {
      this.reportsdocument_public_i18n(lng, bbox, years, months, false, false, categories, hashtag, munis);
    },

    reportsdocument_public_daterange: function(lng, bbox, date_start, date_end, categories, hashtag, munis) {
      this.reportsdocument_public_i18n(lng, bbox, 'all', 'all', date_start, date_end, categories, hashtag, munis);
    },

    reportsdocument_public_i18n: function(lng, bbox, years, months, dateStart, dateEnd, categories, hashtag, munis){
      if (dateStart) dateStart = moment(dateStart).format('YYYY-MM-DD');
      else dateStart ='N'

      if (dateStart) dateEnd = moment(dateEnd).format('YYYY-MM-DD');
      else dateEnd ='N'

      $('.page').hide();
      $('#page-reports').show();
      MOSQUITO.lng = lng;
      new ReportsdocumentView({
          bbox: bbox, years: years, months:months, categories: categories,
          hashtag: hashtag, municipalities: munis,
          daterange: {start: dateStart, end: dateEnd}
        });
    },

    //REPORT DOCUMENTS FOR PRIVATE USERS
    reportsdocument_private_no_daterange: function(lng, bbox, years, months, layers, hashtag, munis, notif, notif_types){
        this.reportsdocument_private_i18n(lng, bbox, years, months, false, false, layers, hashtag, munis, notif, notif_types);
    },

    reportsdocument_private_daterange: function(lng, bbox, dateStart, dateEnd, categories, hashtag, munis, notif, notif_types) {
        this.reportsdocument_private_i18n(lng, bbox, 'all', 'all', dateStart, dateEnd, categories, hashtag, munis, notif, notif_types);
    },

    reportsdocument_private_i18n: function(lng, bbox, years, months, dateStart, dateEnd, categories, hashtag, munis, notif, notif_types){
      if (dateStart) dateStart = moment(dateStart).format('YYYY-MM-DD');
      else dateStart='N'

      if (dateEnd) dateEnd = moment(dateEnd).format('YYYY-MM-DD');
      else dateEnd='N'

      $('.page').hide();
      $('#page-reports').show();
      MOSQUITO.lng = lng;
      new ReportsdocumentView({
          bbox: bbox,
          years: years,
          months:months,
          categories: categories,
          notifications: notif,
          hashtag:hashtag,
          municipalities: munis,
          notif_types: notif_types,
          daterange: {start: dateStart, end: dateEnd}
      });
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
          if (user_layers[i].key === 'M') continue; //do not consider userfixes
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
