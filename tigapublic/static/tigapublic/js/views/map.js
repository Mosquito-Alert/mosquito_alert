var MapView = BaseView.extend({
    el: '#map-view',
    initialize: function(options) {
        options = options || {};
        this.filters = {year: null, months: [], excluded_types: []};
        //_.extend(this.filters, Backbone.Events);
        this.controls = {};
        this.scope = {};
        this.templates = {};
        this.defaults  = {
            zoom: MOSQUITO.config.zoom,
            lon: MOSQUITO.config.lon,
            lat: MOSQUITO.config.lat,
            layers: '0',
        };
        this.options = _.extend({}, this.defaults, options);
        this.options.layers = this.options.layers.split(',').map(Number);

        if('filters_year' in this.options){
            if(this.options.filters_year !== null && this.options.filters_year !== 'all'){
                this.filters.year = parseInt(this.options.filters_year);
            }
        }

        if('filters_months' in this.options){
            if(this.options.filters_months !== null && this.options.filters_months !== 'all'){
                this.filters.months = options.filters_months.split(',').map(Number);
            }
        }

        this.render();
    },

    render: function() {
        //console.debug('Has cridat render', this.options);
        var _this = this;
        var map;

        map = L.map('map', {
            zoomControl: false,
        }).setView([this.options.lat, this.options.lon], this.options.zoom);

        this.map = map;
        window.map = map;

        this.addBaseLayer();
        this.addLayers();

        //addZoomControls
        this.addZoomControl();
        this.addPanelLayersControl();
        this.addFiltersInPanelLayers();

        this.addPanelMoreinfoControl();
        this.addPanelReport();
        this.addPanelShareControl();
        this.addNumReportsControl();

        this.addReportsDocumentControl();

        if(MOSQUITO.config.login_allowed === true){
            this.addPanelDownloadControl();
        }

        this.load_data();

        this.map.on('layerchange', function(layer){
            if (_this.map.hasLayer(layer.layer)) {
                var pos  = this.filters.excluded_types.indexOf(layer.layer._meta.key);
                if(pos !== -1){
                    this.filters.excluded_types.splice(pos, 1);
                }
            }else{
                if(this.filters.excluded_types.indexOf(layer.layer._meta.key) === -1){
                    this.filters.excluded_types.push(layer.layer._meta.key);
                }
            }

            this.drawCluster();

        }, this);

        this.filters.on('year_change', function(year){
            this.filters.year = year;
            //this.drawCluster();
            this.filters.trigger('changed');
        }, this);

        this.filters.on('months_change', function(months){
            this.filters.months = months;
            this.filters.trigger('changed');
        }, this);

        this.filters.on('changed', function(){
            this.drawCluster();
        }, this);

        return this;

    },

    redraw: function(options) {
        if('zoom' in options){
            this.map.setView([options.lat, options.lon], options.zoom);
        }

        if('filters_year' in this.options){
            if(this.options.filters_year !== null && this.options.filters_year !== 'all'){
                this.filters.year = parseInt(this.options.filters_year);
            }
        }

        if('filters_months' in this.options){
            if(this.options.filters_months !== null && this.options.filters_months !== 'all'){
                this.filters.months = options.filters_months.split(',').map(Number);
            }
        }

        if('layers' in options){
            var layers = options.layers.split(',').map(Number);
            this.filters.excluded_types = [];
            for(var i = 0; i < this.LAYERS_CONF.length; i++){
                if(layers.indexOf(i) !== -1){
                    if(this.map.hasLayer(this.LAYERS_CONF[i].layer) === false){
                        this.LAYERS_CONF[i].layer.addTo(this.map);
                    }
                }else{
                    if(this.map.hasLayer(this.LAYERS_CONF[i].layer)){
                        this.map.removeLayer(this.LAYERS_CONF[i].layer);
                    }
                    this.filters.excluded_types.push(this.LAYERS_CONF[i].key);
                }
            }
            this.drawCluster();
        }

    }

});
