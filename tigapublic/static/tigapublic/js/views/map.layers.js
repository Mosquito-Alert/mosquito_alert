var MapView = MapView.extend({

    LAYERS_CONF: MOSQUITO.config.layers,
    stormDrainData :[],
    forceReloadView : true, //Allows pan without reloading data just once. Need to make it false each time
    lastViewWasReload : true, //Tells if last map move reloaded
    userfixtileIndex : null,
    userFixtileOptions :  {
                maxZoom: 20,  // max zoom to preserve detail on
                tolerance: 5, // simplification tolerance (higher means simpler)
                extent: 4096, // tile extent (both width and height)
                buffer: 64,   // tile buffer on each side
                debug: 0,      // logging level (0 to disable, 1 or 2)

                indexMaxZoom: 0,        // max zoom in the initial tile index
                indexMaxPoints: 100000, // max number of points per tile in the index
    },

    addBaseLayer: function(){
        this.layers = this.layers || {};
        this.layers.baselayer = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);
    },


    addLayers: function(){
        var _this = this;
        this.layers = this.layers || {};
        var mcg = new L.MarkerClusterGroup({
            "maxClusterRadius": function (zoom) {
                return (zoom <= MOSQUITO.config.maxzoom_cluster) ? 60 : 30; // radius in pixels
                //return _this.radius;
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

        mcg.addTo(this.map);
        //sometimes it's necessary to overwrite disableClusteringAtZoom. Rethink clustering strategy
        mcg.on('clusterclick', function (a) {
            function createPolygonFromBounds(latLngBounds) {
                latLngBounds = new L.LatLngBounds(latLngBounds.ne, latLngBounds.sw);
                var center =  latLngBounds.getCenter(),
                   latlngs = [];

                 latlngs.push(latLngBounds.getSouthWest());//bottom left
                 //latlngs.push({ lat: latLngBounds.getSouth(), lng: center.lng });//bottom center
                 latlngs.push(latLngBounds.getSouthEast());//bottom right
                 //latlngs.push({ lat: center.lat, lng: latLngBounds.getEast() });// center right
                 latlngs.push(latLngBounds.getNorthEast());//top right
                 //latlngs.push({ lat: latLngBounds.getNorth(), lng: map.getCenter().lng });//top center
                 latlngs.push(latLngBounds.getNorthWest());//top left
                 //latlngs.push({ lat: map.getCenter().lat, lng: latLngBounds.getWest() });//center left

               return new L.polygon(latlngs);
           }


            if (_this.map._zoom < 19) {
                //a.layer.zoomToBounds();
                var bounds = new L.LatLngBounds();
                childs = a.layer.getAllChildMarkers();

                for (var i = 0; i < childs.length; i++){
                        lat = childs[i]._data.lat;
                        lng = childs[i]._data.lon;

                        n = _this.getCurrentGeohashLength();
                        var geohashBounds = Geohash.bounds(Geohash.encode(lat, lng, n));
                        //p = createPolygonFromBounds(geohashBounds);
                        //_this.map.addLayer(p);
                        bounds.extend(new L.LatLngBounds(geohashBounds.ne, geohashBounds.sw));
                }
                _this.map.fitBounds(bounds);
                _this.map.panTo(a.latlng);
            }
            //avoid zoom to cluster, just zoom in
            //_this.map.setView(a.latlng, _this.map.getZoom()+1);
        });

        mcg.on('click', function (e) {
            var report_id = e.layer._data.id;
            if(_this.scope.selectedMarker !== undefined && _this.scope.selectedMarker !== null){
                if(_this.scope.selectedMarker._data.id !== report_id){
                    _this.markerUndoSelected(_this.scope.selectedMarker);
                    _this.scope.selectedMarker = e.layer;
                    _this.markerUndoSelected(e.layer);
                }else{
                    if(_this.report_panel.is(':visible') === false){
                        _this.controls.sidebar.togglePane(_this.report_panel, $('<div>'));
                    }
                    return;
                }
            }

            _this.loading.show(_this.map.latLngToContainerPoint(e.latlng));
            _this.fetch_item(report_id, function(report){
                _this.loading.hide();
                _.extend(e.layer._data, report);
                _this.scope.selectedMarker = e.layer;
                _this.markerSetSelected(_this.scope.selectedMarker);
                _this.show_report(e.layer);
            });

        });

        this.layers.layers = {mcg: mcg};

        // User coverage (user fixes) layer
        userfixeslayer = this.getLayerPositionFromKey('F');
        if (userfixeslayer) this.addCoverageLayer();

        stormdrainlayer = this.getLayerPositionFromKey('Q');
        if (stormdrainlayer) this.addDrainStormLayer();

        var layer, key;

        for (var i = 0; i < this.LAYERS_CONF.length; i++){
            key = this.LAYERS_CONF[i].key;
            layer = L.layerGroup();
            layer._meta = this.LAYERS_CONF[i];
            this.layers.layers[key] = layer;
            if(_.indexOf(this.options.layers, key) !== -1){
                if (key == 'F') {
                    //layer = this.coverage_layer;
                }
                this.map.addLayer(layer);
            }else{
                this.excludeLayerFromFilter(this.LAYERS_CONF[i]);
            }
        }


    },

    getCurrentGeohashLength: function(){
        var hashlength=0,
            zoom = this.map._zoom;

        if (zoom < 4) hashlength = 3;
        else if (zoom < 5) hashlength = 3;
        else if (zoom < 9) hashlength = 4;
        else if (zoom < 12) hashlength = 5;
        else if (zoom < 15) hashlength = 7;
        else hashlength = 8;
        return hashlength;
    },

    getLayerPositionFromKey: function(key) {
        var ret = null;
        for(var i in this.LAYERS_CONF){
            if(this.LAYERS_CONF[i].key === key){
                ret = parseInt(i);
                break;
            }
        }
        return ret;
    },

    getGradientStyle: function(value, layer) {
        // get the segment for the current value
        var found = false, i = 0;
        while (i < layer.segments.length && !found) {
          if (value >= layer.segments[i].from && value <= layer.segments[i].to) found=true;
          else ++i;
        }
        // get the default style
        style = layer.style;
        // overwrite the default style
        if (found) {
          style['fill'+layer.segmentationkey.ucfirst()] = layer.segments[i][layer.segmentationkey];
        } else style['fill'+layer.segmentationkey.ucfirst()] = layer.segments[i-1][layer.segmentationkey];
        return style;
    },
    addDrainStormLayer: function(){
        _this = this;
        this.drainstorm_layer = L.canvasOverlay()
            .drawing(drawingOnCanvas)

        function drawingOnCanvas(canvasOverlay, params) {

            var ctx = params.canvas.getContext('2d');
            ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);

            layer = _this.LAYERS_CONF[_this.getLayerPositionFromKey('Q')];

            //Get dots radius size
            for (var key in layer.radius){
                size = layer.radius[key];
                if (_this.map.getZoom() <= parseInt(key)){
                    size = layer.radius[key];
                    break;
                }
            }

            //Get stroke property
            for (var key in layer.stroke){
                stroke = layer.stroke[key];
                if (_this.map.getZoom() <= parseInt(key)){
                    stroke = layer.stroke[key];
                    break;
                }
            }

            if (stroke){
                ctx.strokeStyle = layer.strokecolor;
                ctx.lineWidth   = layer.strokewidth;
            }
            else{
                ctx.lineWidth   = 0;
            }


            data = _this.stormDrainData.rows;
            colors = _this.stormDrainData.colors;
            var increase = 1;
            if (params.zoomScale < 0.1){
                  increase = Math.floor(1/params.zoomScale/5);
            };

            var pointsdrawn=0;
            for (var i = 0; i < data.length; i+=increase) {
                var d = data[i];
                //d[3]==-1 means no color is applied to object
                if ( (d[2]!=-1) && (params.bounds.contains([d[0], d[1]])) ){

                    dot = canvasOverlay._map.latLngToContainerPoint([d[0], d[1]]);
                    //ctx.fillStyle = (d[2]=="Si")?"rgba(255,0,0, 1)":"rgba(0,255,0, 1)";
                    ctx.fillStyle = colors[d[2]]
                    ctx.beginPath();
                    ctx.arc(dot.x, dot.y, size, 0, Math.PI * 2);
                    ctx.fill();
                    if (stroke) ctx.stroke();
                    ctx.closePath();
                }
                pointsdrawn+=1;
            }
            //Uncomment to see how many points are drawn
            //console.log(params.zoomScale+' '+increase+'  '+pointsdrawn);
        };
    }
    ,
    loadStormDrainData: function(forced){
        //if data not yet loaded
        if (arguments.length==0) {
          forced=false;
        }
        _this = this;
        if (this.stormDrainData.length==0 || forced) {
            url = MOSQUITO.config.URL_API + 'embornals/';
            $.ajax({
                "method": 'GET',
                "async": true,
                "url": url,
                "datatype": 'json',
                "context":this,
            }).done(function(data) {

                this.map.removeLayer(this.drainstorm_layer);
                this.stormDrainData = data;
                //Show legend and data if there is some data

                if (Object.keys(data.style_json).length){
                  this.putStormDrainLegend(data.style_json)
                }

                //add layer even if it is empty
                this.drainstorm_layer.addTo(_this.map);
                /*
                if (data.rows.length){
                  this.drainstorm_layer.addTo(_this.map);
                }
                else{
                  _this.map.removeLayer(this.drainstorm_layer);
                }
                */
                //_this.map.on('click', _this.checkStormDrainInfo);

            });
        }
        //otherwise
        else{
            _this.drainstorm_layer.addTo(_this.map);
            //_this.map.on('click', _this.checkStormDrainInfo);
        }

    },
    checkStormDrainInfo:function(){
      console.log('checkStormDrainInfo');
    }
    ,
    colorizeFeatures: function(arr) {
        _this = this;
        layer = this.LAYERS_CONF[this.getLayerPositionFromKey('F')];
        arr.forEach(function(item){
            pos = (item.properties.num_fixes.toString().length > 4)?3:item.properties.num_fixes.toString().length - 1;
            item.properties.color = 'rgba('+ layer.segments[pos].color+' , '+ layer.segments[pos].opacity +')';
        });
        return true;
    }
    ,
    addCoverageLayer: function() {
        _this = this;
        var pad = 0;

        function drawingOnCanvas(canvasOverlay, params) {
            var bounds = params.bounds;
            params.tilePoint.z = params.zoom;

            var ctx = params.canvas.getContext('2d');
            ctx.globalCompositeOperation = 'source-over';

            if (!_this.userfixtileIndex){
                return;
            }

            var tile = _this.userfixtileIndex.getTile(params.tilePoint.z, params.tilePoint.x, params.tilePoint.y);
            if (!tile) {
                return;
            }
            /*console.log('arguments', arguments);
            console.log('canvasOverlay', canvasOverlay);
            console.log('params', params);
            console.log('tile', tile);*/
            ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);
            var features = tile.features;
            //ctx.strokeStyle = 'grey';

            for (var i = 0; i < features.length; i++) {
                var feature = features[i],
                    type = feature.type;

                ctx.fillStyle = (feature.tags && feature.tags.color)? feature.tags.color : 'rgba(255,0,0,0.05)';
                ctx.strokeStyle = 'rgba(255,0,0,0.1)';
                ctx.beginPath();

                for (var j = 0; j < feature.geometry.length; j++) {
                    var geom = feature.geometry[j];
                    /*if (type === 1) {
                        ctx.arc(geom[0] * ratio + pad, geom[1] * ratio + pad, 2, 0, 2 * Math.PI, false);
                        continue;
                    }*/
                    for (var k = 0; k < geom.length; k++) {
                        var p = geom[k];
                        var extent = 4096;
                        var x = p[0] / extent * 256;
                        var y = p[1] / extent * 256;
                        if (k) ctx.lineTo(x  + pad, y   + pad);
                        else ctx.moveTo(x  + pad, y  + pad);
                    }
                }
                if (type === 3 || type === 1) ctx.fill('evenodd');
                ctx.stroke();
            }
            //if (MOSQUITO.app.mapView) MOSQUITO.app.mapView.loading.off();
        };

        year = this.filters.year || 'all';
        months = (this.filters.months.length>0)?this.filters.months:'all';
        url = MOSQUITO.config.URL_API + 'userfixes/'+year+'/'+months;

        var zeroPoint ={"type": "Point",
            "coordinates": [0,0]};

        _this.userfixtileIndex = geojsonvt(zeroPoint , _this.userFixtileOptions);
        //_this.colorizeFeatures(data);
        _this.coverage_layer = L.canvasTiles()
            .params({ debug: false, padding: 5 })
            .drawing(drawingOnCanvas);

        _this.coverage_layer.addTo(_this.map);
    },

    refreshCoverageLayer: function() {
        layerLI = $('label[i18n="layer.userfixes"]').parent();
        MOSQUITO.app.mapView.loading.on(layerLI);
        _this = this;
        year = this.filters.year || 'all';
        months = (this.filters.months.length>0)?this.filters.months:'all';
        url = MOSQUITO.config.URL_API + 'userfixes/'+year+'/'+months;
        $.ajax({
            "method": 'GET',
            "async": true,
            "url": url
        }).done(function(data) {
            _this.colorizeFeatures(data.features);
            _this.userfixtileIndex = geojsonvt(data, _this.userFixtileOptions);
            _this.map.removeLayer(_this.coverage_layer);
            _this.map.addLayer(_this.coverage_layer);
            //_this.coverage_layer.redraw();
        });
    },

    fetch_data: function(zoom, bbox, callback){
        var url = '';
        //check notification & hashtag filters
        if ( 'hashtag' in this.filters && this.filters.hashtag.trim()!='') {
          hashtag_value = this.filters.hashtag.replace('#','')
          if (hashtag_value =='') hashtag_value='N';
        }
        else hashtag_value='N';

        if ( ('notif' in this.filters && this.filters.notif !== false )  ) {
          if ('notif' in this.filters )
            notif_value = this.filters.notif;
          else notif_value='N';
          url = MOSQUITO.config.URL_API + 'map_aux_reports_bounds/' + bbox + '/' + notif_value +'/'+hashtag_value;
        }
        else if ('notif_types' in this.filters && this.filters.notif_types!==null ) {
          var notif_types = this.filters.notif_types;
          if (notif_types === null) notif_types = 'N';
          else notif_types = notif_types.join(',');
          url = MOSQUITO.config.URL_API + 'get_reports_by_notif_type/' + bbox + '/' + notif_types +'/'+hashtag_value;
        }
        else if ( hashtag_value !=='N'){
            url = MOSQUITO.config.URL_API + 'get_reports_by_notif_type/' + bbox + '/N/'+hashtag_value;
        }
        else if( (zoom >= MOSQUITO.config.maxzoom_cluster) ) {
            url = MOSQUITO.config.URL_API + 'map_aux_reports_bounds/' + bbox;
        }else{
            url = MOSQUITO.config.URL_API + 'map_aux_reports_zoom_bounds/' + zoom+'/'+bbox;
        }

        console.log(url)
        $.ajax({
            method: 'GET',
            url: url
        })
        .done(function(resp) {
            callback(resp);
        })
        .fail(function(error) {
            console.log(error);
        });

    },

    fetch_item: function(id, callback){
        var item;
        /*if(this.map.getZoom()>=MOSQUITO.config.maxzoom_cluster){
            item = _(this.scope.markers).find(function(item){
                if(item._data.id === id){
                    return item;
                }
            });
        }*/

        if(item !== undefined){
            callback(item._data);
        }else{

            $.ajax({
                method: 'GET',
                url: MOSQUITO.config.URL_API + 'map_aux_reports/' + id
            })
            .done(function(resp) {
                callback(resp);
            })
            .fail(function(error) {
                console.log(error);
            });
        }
    },

    load_data: function(){
        var _this = this;
        var search = function(zoom, bbox){
            _this.fetch_data(zoom, bbox, function(data){
                _this.scope.data = data.rows;
                _this.data2markers();
                _this.drawCluster();

            });
        };

        search(this.map.getZoom(), this.map.getBounds().toBBoxString());

        this.map.on('zoomstart',function(){
            _this.scope.markers = [];
            _this.layers.layers.mcg.clearLayers();
        });

        this.map.on('movestart',function(){
            var bbox = _this.map.getBounds().toBBoxString();
            console.log('movestart '+_this.forceReloadView)
            if (_this.forceReloadView){
              if(bbox !== _this.last_bbox){
                  _this.scope.markers = [];
                  _this.layers.layers.mcg.clearLayers();
              }
            }
        });

        this.map.on('moveend',function(){
            var bbox = _this.map.getBounds().toBBoxString();

            if (_this.forceReloadView){
              if(bbox !== _this.last_bbox){
                  if(_this.scope.markers.length > 0){
                      _this.scope.markers = [];
                      _this.layers.layers.mcg.clearLayers();
                  }
                  _this.last_bbox = _this.map.getBounds().toBBoxString();
                  _this.lastViewWasReload = true;
                  search(_this.map.getZoom(), _this.map.getBounds().toBBoxString());
              }
            }
            else{
              _this.forceReloadView = true; //By default, next time data will be reloaded
              _this.lastViewWasReload = false;
            }
        });
    },

    data2markers: function(){
        var _this = this;
        var pos, marker;
        this.scope.markers = [];
        _this.isSelectedMarkerStillLoaded = false;
        _.each(_this.scope.data, function(item){
            var n = 1;
            if(this.map.getZoom()<MOSQUITO.config.maxzoom_cluster){
                n = item.c;
            }

            for(var i = 0; i < n; i++){
                pos = new L.LatLng(item.lat, item.lon);
                marker = _this.getMarkerType(pos, item.category);
                if (marker) {
                  marker._data = item;
                  _this.scope.markers.push(marker);
                  if (_this.scope.selectedMarker){
                      if (marker._data.id == _this.scope.selectedMarker._data.id){
                          _this.isSelectedMarkerStillLoaded = true;
                      }
                  }
                }
            }
        });

        if ( (_this.scope.selectedMarker) && (! _this.isSelectedMarkerStillLoaded) ){
            MOSQUITO.app.mapView.controls.sidebar.closePane();
            _this.scope.selectedMarker = null;
        }

    },

    drawCluster: function(){
        var _this = this;
        var nReports = 0;
        this.layers.layers.mcg.clearLayers();
        var layers = [];
        _.each(this.scope.markers, function(marker){

            if(_this.check_filters(marker)){
                layers.push(_.clone(marker));
                nReports++;
            }
        });
        this.layers.layers.mcg.addLayer(L.layerGroup(layers));
        MOSQUITO.app.trigger('cluster_drawn', {n: nReports});
    },

    check_filters: function(marker){

        excluded_type = this.filters.excluded_types.join(',');

        if(excluded_type.indexOf(marker._data.category) !== -1){
            return false;
        }

        var year = parseInt(marker._data.month.substring(0,4));
        var month = parseInt(marker._data.month.substring(4,6));
        var notif = marker._data.notif;

        //If only year selected, then discard years not selected
        if(this.filters.years.length > 0 && this.filters.months.length == 0){
          if ( _.indexOf(this.filters.years, year) == -1) {
            return false;
          };
        }

        //If only month selected, then discard months not selected
        if (this.filters.years.length ==0 && this.filters.months.length > 0){
          if (_.indexOf(this.filters.months, month) == -1){
            return false;
          };
        }

        //check both and discard not selected ones
        if(this.filters.years.length > 0 && this.filters.months.length > 0){
            if (_.indexOf(this.filters.years, year) == -1
                    || _.indexOf(this.filters.months, month) == -1){
                      return false;
                    };
        }
        //check notification filter
        if('notif' in this.filters) {
            if (this.filters.notif !== false) return notif == this.filters.notif;
            else return true;
        }
        if('notif_types' in this.filters) {
          //console.log(marker._data, this.filters.notif_types);
        }

        return true;
    },

    selectDefaultLayers: function() {
        defaultLayers = this.options.layers;
        this.redraw({layers: defaultLayers});
    },

    getLayerByMarkerCategory: function(category) {
        var i = 0;
        var found = false;
        var retorna = false;

        while (i < this.LAYERS_CONF.length && !found) {
            if ('categories' in this.LAYERS_CONF[i]) {
                for (var cat in this.LAYERS_CONF[i].categories) {
                  var j = 0;
                  while (j < this.LAYERS_CONF[i].categories[cat].length && !found) {
                    if (this.LAYERS_CONF[i].categories[cat][j] == category) {
                        found = true;
                    }
                    else ++j;
                  }
                  if (found) break;
                }
                if (found) retorna = cat;
            }
            if (!found) ++i;
        }
        return retorna;
    },

    getLayerKeyByMarkerCategory: function(category) {
        var i = 0;
        var found = false;
        var key = false;
        while (i < this.LAYERS_CONF.length && !found) {
            if ('categories' in this.LAYERS_CONF[i]) {
                for (var cat in this.LAYERS_CONF[i].categories) {
                  var j = 0;
                  while (j < this.LAYERS_CONF[i].categories[cat].length && !found) {
                    if (this.LAYERS_CONF[i].categories[cat][j] == category) found = true;
                    else ++j;
                  }
                  if (found) break;
                }
                if (found) key = this.LAYERS_CONF[i].key;
            }
            if (!found) ++i;
        }
        return key;
    }

});
