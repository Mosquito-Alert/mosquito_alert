var ReportsdocumentView = MapView.extend({
    el: '#page-reports',

    initialize: function(options) {
        var _this = this;
        options = options || {};
        this.scope = {};
        this.templates = {};

        this.options = _.extend({}, this.defaults, options);
        this.tpl = _.template($('#content-reportsdocument-tpl').text());

        this.is_logged(function(is_logged) {
          _this.render();
        })
    },

    is_logged: function(callback) {
        var _this = this;
        $.ajax({
            type: 'GET',
            'async': true,
            url:  MOSQUITO.config.URL_API + 'ajax_is_logged/',
            success: function(response){
                if (response.success) {
                    _this.LAYERS_CONF = MOSQUITO.config.logged.layers;
                }
                callback(response.success);
            }
        });
    },

    render: function() {
        var _this = this;

        this.fetch_data(this.options, function(data) {
            var iframe_src = opener.MOSQUITO.app.mapView.controls.share_btn.build_url();
            var logged = opener.MOSQUITO.app.headerView.logged;
            if (logged){
                data.license = true
            }
            else{
                data.license = false;
            }

            setTimeout("$('#reports_map_embed').attr('src', '"+iframe_src+"')",1);

            /*$(document).ready(function() {
              $('#reports_map_embed').attr('src', iframe_src);
            });*/

            for(var i = 0; i < data.rows.length; i++){
                row = data.rows[i];

                // hide some fields
                if (opener.MOSQUITO.app.headerView.logged){
                    if(row.t_q_1 != ''){
                        row.t_answers = [];
                        row.questions = [];
                        row.t_answers[0] = row.t_a_1;
                        row.questions[0] = row.t_q_1;
                        if (row.t_q_2 != ''){
                            row.t_answers[1] = row.t_a_2;
                            row.questions[1] = row.t_q_2;
                        }
                        if (row.t_q_3 != ''){
                            row.t_answers[2] = row.t_a_3;
                            row.questions[2] = row.t_q_3;
                        }
                    }
                    if(row.s_q_1 != ''){
                        row.s_answers = [];
                        row.questions = [];
                        row.s_answers[0] = row.s_a_1;
                        row.questions[0] = row.s_q_1;
                        if (row.s_q_2 != ''){
                            row.s_answers[1] = row.s_a_2;
                            row.questions[1] = row.s_q_2;
                        }
                        if (row.s_q_3 != ''){
                            row.s_answers[2] = row.s_a_3;
                            row.questions[2] = row.s_q_3;
                        }
                        if (row.s_q_4 != ''){
                            row.s_answers[3] = row.s_a_4;
                            row.questions[3] = row.s_q_4;
                        }
                    }
                } //not logged
                else {
                    row.note=null;
                }
                if (row.observation_date !== null &&
                    row.observation_date !== '' ){
                        var theDate = new Date(row.observation_date);
                        row.observation_date = theDate.getUTCDate() + '-' + (theDate.getMonth() + 1) + '-' + theDate.getFullYear();
                }

                if(row.expert_validation_result !== null &&
                    row.expert_validation_result.indexOf('#') !== -1){
                    row.expert_validation_result = row.expert_validation_result.split('#');
                    console.log(row.category)
                }

            }

            _this.$el.html(_this.tpl(data));
            window.t().translate(MOSQUITO.lng, _this.$el);

            //Clone TOC and filters from window opener
            //var stuff = window.opener.$("#map_filters").clone();
            var stuff = window.opener.document.getElementById("map_filters").outerHTML;
            $('#map_filters').html(stuff);

            var stuff = window.opener.document.getElementById("hashtag_filters").outerHTML;
            var hastag_opener_value = window.opener.document.getElementById("hashtag_search_text").value;

            // if (hastag_opener_value.length){
            //    if (hastag_opener_value.trim()!=''){
            //      $('#hashtag_search_text').val(hastag_opener_value);
            //      $('#hashtag_search_text').prop('disabled',true);
            //     }
            //   }

            //Disable hashtack and  municipalities boxes
            $('#hashtag_search_text').prop('disabled',true);
            $('#municipality_group').find('input').prop('disabled', true)

            //var stuff = window.opener.$("#notif_filters").clone();
            if (window.opener.document.getElementById("notif_filters")){
              var stuff = window.opener.document.getElementById("notif_filters").innerHTML;
              $('#notif_filters').html(stuff);
              $( "input[name='notification_radio']" ).prop('disabled',true);
            }

            if (window.opener.document.getElementById("map_layers_list")){
              var stuff = $('<div>').html(window.opener.document.getElementById("map_layers_list").outerHTML).find('li.active');
              //except models and background layers
              stuff = $(stuff).not('#layer_I, #layer_F');
              stuff.removeClass('active');
            }


            //Remove municipalities cancel x
            $('div.token a.close').remove()
            $('span.token-label').css('padding-right','4px')


            $('#map_layers').html(stuff);
            //remove some unnecessary sublist elements
            $('#map_layers > li.sublist-group-item').remove();
            // remove userfixes layer

            if (MOSQUITO.config.keyLayersExcludedFromSharingURL.length){
              MOSQUITO.config.keyLayersExcludedFromSharingURL.forEach(function(e){
                  $('#map_layers > li#layer_'+e).parent().remove();
              })

            }

            $('#legend_reports_map button').addClass('disabled');

            // Create header map

            var mapView = window.opener.MOSQUITO.app.mapView;

            var z = mapView.map.getZoom() - 1; // the map is smaller so we need to zoom out
            var c = mapView.map.getCenter();
            var b = mapView.map.getBounds();

            var theMap = L.map('reports_header_map', { zoomControl:false})
                .setView(c,z);

            L.tileLayer('//{s}.tile.osm.org/{z}/{x}/{y}.png', {
                    minZoom: z, // prevent from zooming
                    maxZoom: z,
                    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(theMap);

            theMap.dragging.disable()

            var layers=[];
            var row, center, map;
            // Create all maps

            for(i = 0; i < data.rows.length; i++){
                row = data.rows[i];
                //if notif is checked and observation has no notif, then skip observation
                if ($('#checkbox_notif').is(':checked')
                    && row.notif!="1"){
                      continue;
                }
                center  = [row.lat, row.lon];
                map = L.map('map_report_' + row.id, { zoomControl:false}).
                    setView(center, 16);

                L.tileLayer('//{s}.tile.osm.org/{z}/{x}/{y}.png', {
                        maxZoom: 18,
                        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                    }).addTo(map);
                L.marker(center, {icon: _this.getIconType(row.private_webmap_layer)}).addTo(map);
                layers.push(L.marker(center, {icon: _this.getIconType(row.private_webmap_layer)}));
            }

            // Create Marker cluster group and add its makers
            var mcg = new L.MarkerClusterGroup({
              "maxClusterRadius": function (zoom) {
                  return (zoom <= MOSQUITO.config.maxzoom_cluster) ? 180 : 30; // radius in pixels
              },
                "chunkedLoading": true,
                "spiderfyOnMaxZoom": true,
                "showCoverageOnHover": MOSQUITO.config.showCoverageOnHover,
              //disableClusteringAtZoom: MOSQUITO.config.maxzoom_cluster,
              "iconCreateFunction": function(cluster) {
                  var markerCount = cluster._childCount;
                  var r = markerCount.toString().length;
                  var className = '';
                  switch (r) {
                    case 1: className = 'marker-cluster-radius20'; break;
                    case 2: className = 'marker-cluster-radius30'; break;
                    case 3: className = 'marker-cluster-radius40'; break;
                    case 4: className = 'marker-cluster-radius50'; break;
                    case 5: className = 'marker-cluster-radius60'; break;
                  }
                  return new L.DivIcon({html: '<div class=" leaflet-marker-icon '+className+' marker-cluster-medium leaflet-zoom-animated leaflet-clickable" tabindex="0"><div><span>'+markerCount+'</span></div></div>'});
              }
            });

            mcg.addLayer(L.layerGroup(layers));
            mcg.addTo(theMap);

            theMap.fitBounds(mcg.getBounds());
        });
        return this;

    },

    isDaterangeEmpty: function(o){
      return (
        typeof o.daterange.start == 'undefined' ||
        typeof o.daterange.end == 'undefined' ||
        o.daterange.start == 'N' ||
        o.daterange.end == 'N'
      )
    },

    fetch_data: function(options, callback){
        url = MOSQUITO.config.URL_API + 'observations/report/' + options.bbox + '/';

        if (!this.isDaterangeEmpty(options)) {
          url += options.daterange.start + '/' + options.daterange.end;
        } else {
          url += options.years + '/' + options.months;
        }
        url += '/' + options.categories ;

        if ('hashtag' in options){
          hashtag = options.hashtag.replace('#','');
          if (hashtag==''){
            hashtag='N'
          }
        }else{
          hashtag = 'N';
        }
        url += '/'+hashtag;

        //check municipalities
        if ('municipalities' in options){
          municipalities = options.municipalities;
        }else{
          municipalities = 'N';
        }
        url += '/' + municipalities;

        //my notifications
        url += (('notifications' in options) && (options.notifications !== "false" ))?'/' + options.notifications:'/N';

        //Notifications types
        url += (('notif_types' in options) && (options.notif_types !== null ))?'/' + options.notif_types:'/N';

        $.ajax({
            method: 'GET',
            url: url

        })
        .done(function(resp) {
            callback(resp);
        })
        .fail(function(error) {
            if (console && console.error) console.error(error);
        });

    },


});
