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
            layers: MOSQUITO.config.default_layers,
        };
        // get the admin layers if we are logged in
        if ('logged' in MOSQUITO.app.headerView  && MOSQUITO.app.headerView.logged) {
            //MOSQUITO.config.layers = MOSQUITO.config.logged.layers;
            this.LAYERS_CONF = MOSQUITO.config.logged.layers;
        }
        this.options = _.extend({}, this.defaults, options);
        //console.log(this.options);
        //this.options.layers = this.options.layers.split(',').map(Number);
        this.options.layers = this.options.layers.split(',');

        if('filters_year' in this.options){
            if(this.options.filters_year !== null && this.options.filters_year !== 'all' && parseInt(this.options.filters_year)){
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

        //xapussilla??
        if (MOSQUITO.config.printreports) this.addReportsDocumentControl();

        this.selectDefaultLayers();

        if (typeof MOSQUITO.config.minZoom != 'undefined') {
            this.map.options.minZoom = MOSQUITO.config.minZoom;
        }

        if ('lock_bounds' in MOSQUITO.config) {
            if (typeof MOSQUITO.config.lock_bounds == 'boolean' && MOSQUITO.config.lock_bounds === true) {
              // get bounds from the current map view
              bounds = bufferedBounds(this.map.getBounds(),1);
            } else {
              // get bounds from config file
              var southWest = L.latLng(MOSQUITO.config.lock_bounds.ymin, MOSQUITO.config.lock_bounds.xmin),
                  northEast = L.latLng(MOSQUITO.config.lock_bounds.ymax, MOSQUITO.config.lock_bounds.xmax),
                  bounds = L.latLngBounds(southWest, northEast);
            }
            this.map.setMaxBounds(bounds);
        }

        if(MOSQUITO.config.login_allowed === true){
            this.addPanelDownloadControl();
        }

        this.load_data();

        this.map.on('layerchange', function(layer){
            if (_this.map.hasLayer(layer.layer)) {
              this.options.layers.push(layer.layer._meta.key);
              if ('categories' in layer.layer._meta) {
                for (var cat in layer.layer._meta.categories) {
                  for(i=0;i<layer.layer._meta.categories[cat].length;++i) {
                    var pos = this.filters.excluded_types.indexOf(layer.layer._meta.categories[cat][i]);
                    if(pos !== -1){
                        this.filters.excluded_types.splice(pos, 1);
                    }
                  }
                }
              } else {
                var pos  = this.filters.excluded_types.indexOf(layer.layer._meta.key);
                if(pos !== -1){
                    this.filters.excluded_types.splice(pos, 1);
                }
              }
            }else{
              this.options.layers.splice(this.options.layers.indexOf(layer.layer._meta.key), 1);
              this.excludeLayerFromFilter(layer.layer._meta);
            }

            this.drawCluster();

        }, this);

        this.filters.on('year_change', function(year){
            this.filters.year = year;
            this.filters.trigger('changed');
        }, this);

        this.filters.on('months_change', function(months){
            this.filters.months = months;
            this.filters.trigger('changed');
        }, this);

        this.filters.on('changed', function(){
            this.refreshCoverageLayer();
            this.drawCluster();
        }, this);

        return this;

    },

    redraw: function(options) {
        if('zoom' in options){
            this.map.setView([options.lat, options.lon], options.zoom);
        }

        if('filters_year' in this.options){
            if(this.options.filters_year !== null && this.options.filters_year !== 'all' && parseInt(this.options.filters_year)){
                this.filters.year = parseInt(this.options.filters_year);
            }
        }

        if('filters_months' in this.options){
            if(this.options.filters_months !== null && this.options.filters_months !== 'all'){
                this.filters.months = this.options.filters_months.split(',').map(Number);
            }
        }
        if('layers' in options){

            /*
            if (typeof options.layers == 'string') var layers = options.layers.split(',').map(Number);
            else var layers = options.layers;
            */
            var layers = options.layers;
            this.filters.excluded_types = [];
            for(var i = 0; i < this.LAYERS_CONF.length; i++){
                key = this.LAYERS_CONF[i].key;
                if(layers.indexOf(key) !== -1){
                    if(this.map.hasLayer(this.LAYERS_CONF[i].layer) === false){
                        this.LAYERS_CONF[i].layer.addTo(this.map);
                    }
                }else{
                    if(this.map.hasLayer(this.LAYERS_CONF[i].layer)){
                        this.map.removeLayer(this.LAYERS_CONF[i].layer);
                    }
                    this.excludeLayerFromFilter(this.LAYERS_CONF[i]);
                }
            }

            this.drawCluster();
        }

    },

    excludeLayerFromFilter: function(layer) {
      if ('categories' in layer) {
        for (var cat in layer.categories) {
          for(i=0;i<layer.categories[cat].length;++i) {
            if(this.filters.excluded_types.indexOf(layer.categories[cat][i]) === -1){
              this.filters.excluded_types.push(layer.categories[cat][i]);
            }
          }
        }
      } else {
        if(this.filters.excluded_types.indexOf(layer.key) === -1){
          this.filters.excluded_types.push(layer.key);
        }
      }

    }

});
