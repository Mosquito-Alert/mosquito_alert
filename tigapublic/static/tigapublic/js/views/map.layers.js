var MapView = MapView.extend({

    LAYERS_CONF: MOSQUITO.config.layers,

    addBaseLayer: function(){
        this.layers = this.layers || {};
        this.layers.baselayer = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);
    },


    addLayers: function(){
        marc =this;
        var _this = this;
        this.layers = this.layers || {};

        var mcg = new L.MarkerClusterGroup({
          "maxClusterRadius": function (zoom) {
              //return (MOSQUITO.config.clusterize ? 180:1);
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

            //<----Mirem si hem de desplaçar
            var w0 = _this.map.getSize().x;
            var w1 = w0 - 500;
            var x100 = 100*w1/w0;
            var b = _this.map.getBounds();
            var distance = b.getEast() - b.getWest();
            var d = distance / 100 * x100;
            var bb0 = L.latLngBounds(b.getSouthWest(), [b.getNorth(), b.getWest() + d]);
            if(bb0.contains(e.layer.getLatLng())===false){
                //var bb1 = L.latLngBounds([b.getSouth(), b.getWest() + d, b.getNorthEast()]);
                //_this.map.setView([_this.map.getCenter().lat, bb1.getCenter().lng], _this.map.getZoom());
                //var bb1 = L.latLngBounds([b.getSouth(), b.getWest() + d, b.getNorthEast()]);
                _this.map.setView([_this.map.getCenter().lat, e.layer.getLatLng().lng], _this.map.getZoom());
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

    addCoverageLayer: function() {
        _this = this;
        this.coverage_layer = L.geoJson(false, {
            "style": function(feature) {
                layerid = _this.getLayerPositionFromKey('F');
                return _this.getGradientStyle(feature.properties.num_fixes, _this.LAYERS_CONF[layerid]);
            },
            "onEachFeature": function(feature, layer) {
                if ('num_fixes' in feature.properties) {
                  layer.bindPopup('<div style="white-space:nowrap;"><span i18n="map.numfixes">'+t('map.numfixes')+'</span>: '+feature.properties.num_fixes+'</div>');
                }
            }
        }).addTo(this.map);
        this.map.removeLayer(this.coverage_layer);

        this.coverage_layer.on('click', function (e) {
            t().translate($('html').attr('lang'), $('.leaflet-popup-pane'));
        });
        this.refreshCoverageLayer();
    },

    refreshCoverageLayer: function() {
        _this = this;
        year = this.filters.year || 'all';
        months = (this.filters.months.length>0)?this.filters.months:'all';
        url = MOSQUITO.config.URL_PUBLIC + 'userfixes/'+year+'/'+months;
        $.ajax({
            "method": 'GET',
            "async": true,
            "url": url
        }).done(function(resp) {
            _this.coverage_layer.clearLayers();
            _this.coverage_layer.addData(resp);
            if (_this.controls.layers_btn.getSelectedKeys().indexOf('F') > -1) {
              _this.map.addLayer(_this.coverage_layer);
            }
        });
    },

    fetch_data: function(zoom, bbox, callback){
        var url = '';
        if(zoom >= MOSQUITO.config.maxzoom_cluster){
            url = MOSQUITO.config.URL_API + 'map_aux_reports_bounds/' + bbox;
        }else{
            url = MOSQUITO.config.URL_API + 'map_aux_reports_zoom_bounds/' + zoom+'/'+bbox;
        }

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
                url: MOSQUITO.config.URL_PUBLIC + 'map_aux_reports/' + id
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
                }
            );
        };

        search(this.map.getZoom(), this.map.getBounds().toBBoxString());

        this.map.on('zoomstart',function(){
            _this.scope.markers = [];
            _this.layers.layers.mcg.clearLayers();
        });

        this.map.on('movestart',function(){
            var bbox = _this.map.getBounds().toBBoxString();
            if(bbox !== _this.last_bbox){
                _this.scope.markers = [];
                _this.layers.layers.mcg.clearLayers();
            }
        });

        this.map.on('moveend',function(){
            var bbox = _this.map.getBounds().toBBoxString();
            if(bbox !== _this.last_bbox){
                if(_this.scope.markers.length > 0){
                    _this.scope.markers = [];
                    _this.layers.layers.mcg.clearLayers();
                }
                _this.last_bbox = _this.map.getBounds().toBBoxString();
                search(_this.map.getZoom(), _this.map.getBounds().toBBoxString());
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

        /*for(var i = 0; i < this.filters.excluded_types.length; i++){
            excluded_type=this.filters.excluded_types[i];
            if(marker._data.category.indexOf(excluded_type) !== -1){
                return false;
            }
        }
        */

        var year = parseInt(marker._data.month.substring(0,4));
        var month = parseInt(marker._data.month.substring(4,6));

        if(this.filters.year !== null && year !== this.filters.year){
            return false;
        }
        if(this.filters.months.length > 0){
            return _.indexOf(this.filters.months, month) !== -1;
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
