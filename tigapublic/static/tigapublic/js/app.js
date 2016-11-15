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
            this.route(/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/([\d,]*)\/([\d]*|all)\/([\d,]*|all)\/?$/, 'map');
            //$zoom/$lat/$lon/$layers/$year/$months/$report
            this.route(/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/([\d,]*)\/([\d-]*|all)\/([\d,]*|all)\/([\d]*)\/?$/, 'report');

            //$lng/
            this.route(/([a-z]{2})\/?$/, 'map_i18n');
            //$lng/$zoom/$lat/$lon/
            this.route(/([a-z]{2})\/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/?$/, 'map_i18n');
            //$lng/$zoom/$lat/$lon/$layers/$year/$months
            this.route(/([a-z]{2})\/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/([\d,]*)\/([\d]*|all)\/([\d,]*|all)\/?$/, 'map_i18n');
            //$lng/$zoom/$lat/$lon/$layers/$year/$months/$report
            this.route(/([a-z]{2})\/(\d\d|\d)\/(-?\d+\.?\d*)\/(-?\d+\.?\d*)\/([\d,]*)\/([\d]*|all)\/([\d,]*|all)\/([\d]*)\/?$/, 'report_i18n');

            // this.route(/reportsdocument\/(-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*)\/(.*)\/(.*)\/(.*)\/?$/, 'reportsdocument');
            // this.route(/([a-z]{2})\/reportsdocument\/(-?\d+\.?\d*-?\d+\.?\d*-?\d+\.?\d*-?\d+\.?\d*)\/(.*)\/(.*)\/(.*)\/?$/, 'reportsdocument_i18n');

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

        map: function(zoom, lat, lon, layers, year, months) {
            this.map_i18n(MOSQUITO.config.default_lng, zoom, lat, lon, layers, year, months);
        },

        map_i18n: function(lng, zoom, lat, lon, layers, year, months) {
            if($('#page-map').is(':hidden')){
                $('.page').hide();
                $('#page-map').show();
            }
            var options = {};
            if(zoom !== undefined && lat !== undefined && lon !== undefined){
                options.zoom = zoom;
                options.lat = lat;
                options.lon = lon;
            }

            if(layers !== undefined && layers !== null && layers.length > 0){
                options.layers = layers;
            }

            if(year !== undefined && year !== 'all'){
                options.filters_year = year;
            }

            if(months !== undefined && months !== 'all'){
                options.filters_months = months;
            }

            if(!this.headerView){
                this.headerView = new HeaderView();
            }

            if(!this.mapView){
                this.mapView = new MapView(options);
            }else{
                //console.debug('TODO: Cal aplicar noves condicions');
                this.mapView.redraw(options);
            }

            if(lng !== last_lang){
                t().change(lng);
            }
            last_lang = lng;
        },

        report: function(lng, zoom, lat, lon, layers, year, months, report_id){
            this.report_i18n(MOSQUITO.config.default_lng, lng, zoom, lat, lon, layers, year, months, report_id);
        },

        report_i18n: function(lng, zoom, lat, lon, layers, year, months, report_id){
            var _this = this;
            var show_report;
            show_report = function(){
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
                            originalEvent: {
                                pageX: p.left + w/2,
                                pageY: p.top
                            }
                        }
                    );
                }
                this.off('cluster_drawn', show_report);
            };

            this.on('cluster_drawn', show_report);
            this.map_i18n(lng, zoom, lat, lon, layers, year, months);

        },

        reportsdocument: function(bbox, years, months, excluded_types){
            this.reportsdocument_i18n(MOSQUITO.config.default_lng, bbox, years, months, excluded_types);
        },

        reportsdocument_i18n: function(lng, bbox, years, months, excluded_types){
            $('.page').hide();
            $('#page-reports').show();
            new ReportsdocumentView({bbox: bbox, year: years, months:months, excluded_types: excluded_types});
            //window.location.hash = '#/' + last_lang;
        }

    });

    MOSQUITO.app = new AppRouter();
    Backbone.history.start();



}(Backbone, jQuery, MOSQUITO || {}));
