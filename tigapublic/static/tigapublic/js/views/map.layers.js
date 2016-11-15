var MapView = MapView.extend({

    LAYERS_CONF: [
        {
            key: 'albopictus',
            title: 'layer.tiger'//,
            //visible: true,
            //icon: this.getIconUrl(this.key)
        }, //albopictus
        {
            key: 'aegypti',
            title: 'layer.zika'//,
            //visible: true,
            //icon: 'img/marker_zika.svg'
        }, //aegypti
        {
            key: 'noseparece',
            title: 'layer.noparece'//,
            //visible: false,
            //icon: 'img/marker_noparece.svg'
        },
        {
            key: 'nosesabe',
            title: 'layer.nosabe'//,
            //visible: false,
            //icon: 'img/marker_nosabe.svg'
        },
        {
            key: 'site',
            title: 'layer.site'//,
            //visible: false,
            //icon: 'img/marker_site.svg'
        }
    ],

    addBaseLayer: function(){
        this.layers = this.layers || {};
        this.layers.baselayer = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);
    },


    addLayers: function(){
        var _this = this;
        this.layers = this.layers || {};

        var mcg = new L.MarkerClusterGroup({
        	chunkedLoading: true,
        	spiderfyOnMaxZoom: false,
        	showCoverageOnHover: false,
            disableClusteringAtZoom: MOSQUITO.config.maxzoom_cluster,
            iconCreateFunction: function(cluster) {
                //console.debug(cluster);
                //var markers = cluster.getAllChildMarkers();
                var markerCount = cluster._childCount;
                /*
                var markerCount = 0;
                var i;
                for(i in markers){
                    markerCount = markerCount + markers[i]._data.c;
                }
                */
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
            // a.layer is actually a cluster
            a.layer.zoomToBounds();

        });
        mcg.on('click', function (e) {

            var report_id = e.layer._data.id;

            if(_this.scope.selectedMarker !== undefined && _this.scope.selectedMarker !== null){
                if(_this.scope.selectedMarker._data.id !== report_id){
                    _this.markerUndoSelected(_this.scope.selectedMarker);
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
            //----<<

            _this.loading.show(e);
            _this.fetch_item(report_id, function(report){
                _this.loading.hide();
                _.extend(e.layer._data, report);
                _this.scope.selectedMarker = e.layer;
                //TODO: S'ha de treure

                _this.show_report(e.layer);
            });

        });

        this.layers.layers = {mcg: mcg};

        var layer, key;
        for (var i = 0; i < this.LAYERS_CONF.length; i++){
            key = this.LAYERS_CONF[i].key;
            //layer = L.featureGroup.subGroup(mcg);
            layer = L.layerGroup();
            layer._meta = this.LAYERS_CONF[i];
            this.layers.layers[key] = layer;
            if(_.indexOf(this.options.layers, i) !== -1){
                this.map.addLayer(layer);
            }else{
                this.filters.excluded_types.push(key);
            }
        }
    },


    fetch_data: function(zoom, bbox, callback){
        var url = '';
        if(zoom >= MOSQUITO.config.maxzoom_cluster){
            url = MOSQUITO.config.URL_API + 'map_aux_reports_bounds/' + bbox;
        }else{
            url = MOSQUITO.config.URL_API + 'map_aux_reports_zoom_bounds/' + zoom+'/'+bbox;
        }

        //url = MOSQUITO.config.URL_API + 'bounds/' + zoom+'/'+bbox;

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
        if(this.map.getZoom()>=MOSQUITO.config.maxzoom_cluster){
            item = _(this.scope.markers).find(function(item){
                if(item._data.id === id){
                    return item;
                }
            });
        }

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
        _.each(_this.scope.data, function(item){
            var n = 1;
            if(this.map.getZoom()<MOSQUITO.config.maxzoom_cluster){
                n = item.c;
            }
            for(var i = 0; i < n; i++){
                pos = new L.LatLng(item.lat, item.lon);
                marker = _this.getMarkerType(pos, item.simplified_expert_validation_result);
                marker._data = item;
                _this.scope.markers.push(marker);
            }

        });

    },

    drawCluster: function(){
        var _this = this;
        var nReports = 0;
        this.layers.layers.mcg.clearLayers();
        var layers = [];
        _.each(this.scope.markers, function(marker){
            if(_this.check_filters(marker)){
                //_.clone(marker).addTo(_this.layers.layers.mcg);
                layers.push(_.clone(marker));
                nReports++;
            }
        });
        this.layers.layers.mcg.addLayer(L.layerGroup(layers));
        //this.map.fire('cluster_drawn', {n: nReports});
        MOSQUITO.app.trigger('cluster_drawn', {n: nReports});
    },

    check_filters: function(marker){

        /*
        if(this.filters.excluded_types.indexOf(marker._data._type) !== -1){
            return false;
        }
        */
        var excluded_type;
        for(var i = 0; i < this.filters.excluded_types.length; i++){
            excluded_type=this.filters.excluded_types[i];
            if(marker._data.simplified_expert_validation_result.indexOf(excluded_type) !== -1){
                return false;
            }
        }
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


});
