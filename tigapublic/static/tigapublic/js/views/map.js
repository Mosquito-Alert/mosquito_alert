  var MapView = BaseView.extend({
    el: '#map-view',
    initialize: function(options) {
        options = options || {};
        this.filters = {
            years: [],
            months: [],
            excluded_types: [],
            hashtag:'N',
            municipalities:'N'
          };
        //_.extend(this.filters, Backbone.Events);
        this.controls = {};
        this.scope = {'allowDataLoading': true};
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
            MOSQUITO.config = _.extend(MOSQUITO.config, MOSQUITO.config.logged);

        }
        this.options = _.extend({}, this.defaults, options);

        //this.options.layers = this.options.layers.split(',').map(Number);
        this.options.layers = this.options.layers.split(',');

        if('filters_years' in this.options){
            if(this.options.filters_years !== null && this.options.filters_years !== 'all'){
                this.filters.years = options.filters_years.split(',').map(Number);
            }
        }
        if('filters_months' in this.options){
            if(this.options.filters_months !== null && this.options.filters_months !== 'all'){
                this.filters.months = options.filters_months.split(',').map(Number);
            }
        }
        if('filters_daterange' in this.options){
            if(this.options.filters_daterange !== null){
                this.filters.daterange = options.filters_daterange;
            }
        }

        if('filters_hashtag' in this.options){
            if(this.options.filters_hashtag != 'N'){
                this.filters.hashtag = this.options.filters_hashtag;
            }
        }

        if('filters_municipalities' in this.options){
            if (!MOSQUITO.app.headerView.logged &&
                    options.filters_municipalities == '0'){
                this.filters.municipalities = 'N';
            }
            else {
                this.filters.municipalities = options.filters_municipalities;
            }
        }
        this.render();
    },

    userCan: function(role) {
      role_groups = MOSQUITO.config.roles[role];
      if ('groups' in MOSQUITO.app.user) {
        var i = 0, found = false;
        user_groups = MOSQUITO.app.user.groups;
        role_groups.forEach(function(role_group){
            user_groups.forEach(function(user_group){
                if (user_group == role_group) {
                    found=true;
                }
            });
        });
        return found;
      } else return false;
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
        this.addPanelEpidemiology();
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
        //Not registered users get to download data
          this.addPanelDownloadControl();

        if(MOSQUITO.config.login_allowed === true && MOSQUITO.app.headerView.logged){

            if (this.userCan('notification')) {
              this.addNotificationControl();
              //this.addRoleFunctions();
            }
        }

        if (this.dataLoadingIsAllowed()){
          this.load_data();
        }

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

            if ('notificationServerIds' in MOSQUITO.app.mapView.scope) {
                this.controls.notification.getNotificationClientIds();
            }
            this.drawCluster();
        }, this);

        this.filters.on('years_change', function(years) {
            this.filters.years = years;
            this.filters.trigger('changed','year');
        }, this);

        this.filters.on('months_change', function(months){
            this.filters.months = months;
            this.filters.trigger('changed','months');
        }, this);

        this.filters.on('notif_change', function(notif){
            //this.filters.notif = notif?'1':'0';
            this.filters.notif = notif;
            this.filters.notif_types = ['N'];
            this.filters.trigger('changed','notif');
        }, this);

        this.filters.on('notif_type_change', function(notif_types){
            //this.filters.notif = notif?'1':'0';
            this.filters.notif = false;
            this.filters.notif_types = notif_types;
            this.filters.trigger('changed','notif_types');
        }, this);

        this.filters.on('hashtag_change', function(search_text){
          this.filters.hashtag = search_text;
          this.filters.trigger('changed','hashtag');
        }, this);

        this.filters.on('daterange_change', function(range){
          this.filters.daterange = range;
          this.filters.trigger('changed','daterange');
        }, this)

        this.filters.on('municipalities_change', function(municipalities){
          this.filters.municipalities = municipalities;
          this.filters.trigger('changed','municipalities');
        }, this)

        this.filters.on('changed', function(filter) {
          //filter epidata
          if (this.hasDateFilterChanged(filter)
              && (this.map.hasLayer(this.epidemiology_layer)) ) {
              this.epidemiology_filter();
          }
          var newCallFilters = [
            'notif', 'hashtag', 'notif_types', 'municipalities', 'daterange'
          ];
          var userfixCallFilters = ['year', 'years', 'months', 'daterange'];
          if (userfixCallFilters.indexOf(filter) !== -1) {
              if (this.map.hasLayer(this.coverage_layer)) {
                this.refreshCoverageLayer();
              }
          }
          if (newCallFilters.indexOf(filter) === -1) {
              this.drawCluster();
              // make an exception for daterange and load observations
          } else {
            if (this.dataLoadingIsAllowed()){
              this.load_data();
            }
          }
          if (this.anyFilterChecked()){
            this.activateFilterAcordion();
          }
          else{
            this.deactivateFilterAcordion();
          }
        }, this);
        return this;
    },

    redraw: function(options) {

        if('zoom' in options){
            this.map.setView([options.lat, options.lon], options.zoom);
        }

        if('filters_years' in this.options){
            if(this.options.filters_years !== null && this.options.filters_years !== 'all'){
                this.filters.years = this.options.filters_years.split(',').map(Number);
            }
        }

        if('filters_months' in this.options){
            if(this.options.filters_months !== null && this.options.filters_months !== 'all'){
                this.filters.months = this.options.filters_months.split(',').map(Number);
            }
        }
        if('filters_daterange' in this.options){
            if(this.options.filters_daterange !== null){
                this.filters.daterange = this.options.filters_daterange;
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
    },
    /**
     * @return {boolean} true if (lng, lat) is in bounds
     */
    isPointInPolygon: function(bounds, lat, lng) {
        //https://rosettacode.org/wiki/Ray-casting_algorithm
        var count = 0;
        for (var b = 0; b < bounds.length; b++) {
            var vertex1 = bounds[b];
            var vertex2 = bounds[(b + 1) % bounds.length];
            if (west(vertex1, vertex2, lng, lat))
                ++count;
        }
        return count % 2;

        /**
         * @return {boolean} true if (x,y) is west of the line segment connecting A and B
         */
        function west(A, B, x, y) {
            if (A.lat <= B.lat) {
                if (y <= A.lat || y > B.lat ||
                    x >= A.lng && x >= B.lng) {
                    return false;
                } else if (x < A.lng && x < B.lng) {
                    return true;
                } else {
                    return (y - A.lat) / (x - A.lng) > (B.lat - A.lat) / (B.lng - A.lng);
                }
            } else {
                return west(B, A, x, y);
            }
        }
    },

    setDataLoading: function(state){
      this.scope.allowDataLoading = state
    },

    dataLoadingIsAllowed: function(){
      return (this.scope.allowDataLoading)
    },

    hasDateFilterChanged: function(filter){
      return (['year','months','daterange'].indexOf(filter)!==-1)
    }
});
