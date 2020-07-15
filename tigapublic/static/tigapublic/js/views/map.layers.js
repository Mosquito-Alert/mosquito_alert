var MapView = MapView.extend({
    LAYERS_CONF: MOSQUITO.config.layers,
    stormDrainData :[],
    forceReloadView : true, //Allows pan without reloading data just once. Need to make it false each time
    lastViewWasReload : true, //Tells if last map move reloaded
    userfixtileIndex : null,
    userFixtileOptions :  {
        maxZoom: 20,  // max zoom to preserve detail on
        tolerance: 2, // simplification tolerance (higher means simpler)
        extent: 4096, // tile extent (both width and height)
        buffer: 64,   // tile buffer on each side
        debug: 0,      // logging level (0 to disable, 1 or 2)

        indexMaxZoom: 0,        // max zoom in the initial tile index
        indexMaxPoints: 100000, // max number of points per tile in the index
    },

    addBaseLayer: function(){
        this.layers = this.layers || {};
        this.layers.baselayer = L.tileLayer('//{s}.tile.osm.org/{z}/{x}/{y}.png', {
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
        if (userfixeslayer!==null) this.addCoverageLayer(userfixeslayer);

        stormdrainlayer = this.getLayerPositionFromKey('Q');
        if (stormdrainlayer!==null) this.addDrainStormLayer();

        forecastMunisLayer = this.getLayerPositionFromKey('M');
        if (forecastMunisLayer!==null) {
          this.loadVectorProbMunisModel();
          this.loadForecastModel();
        }

        forecastVirusLayer = this.getLayerPositionFromKey('N');
        if (forecastVirusLayer!==null) this.loadVirusProbMunisModel();

        bitingLayer = this.getLayerPositionFromKey('R');
        if (bitingLayer!==null) this.addBitingLayer(bitingLayer);

        //empty layergroup for epidemiology data
        epilayer = this.LAYERS_CONF[this.getLayerPositionFromKey('P')];
        if (epilayer){
          this.epidemiology_layer = L.layerGroup()
          this.epidemiology_palette=epilayer.palettes[epilayer.default_palette]
          _this.epidemiology_palette_date = 'date_arribal'
          $('#epidemiology_palette_form').click(function(e){
            $('#epidemiology_form_setup').modal('hide');
            _this.addEpidemiologyLayer()
            $('#layer_P').addClass('active');
          })
        }

        var layer, key;

        for (var i = 0; i < this.LAYERS_CONF.length; i++){
            key = this.LAYERS_CONF[i].key;
            layer = L.layerGroup();
            layer._meta = this.LAYERS_CONF[i];
            this.layers.layers[key] = layer;
            if(_.indexOf(this.options.layers, key) !== -1){
                if (key == 'F') {
                  this.refreshCoverageLayer();
                } else if (key === 'M') {
                  //check if grid is active
                  var modelType = $("input[name='modelType']:checked").val();
                  if (modelType=='grid'){
                    this.refreshForecastModel();
                  }
                } else this.map.addLayer(layer);
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

    getLayerFromKey: function (key){
            return this.LAYERS_CONF[this.getLayerPositionFromKey(key)];
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

    getEpidemiologyPatientStateIcon: function(patientRow){
      epilayer = this.LAYERS_CONF[this.getLayerPositionFromKey('P')];
      var palette = epilayer.palettes.patient_states
      var field = palette.column
      return this.getEpidemiologyIconUrl(patientRow, palette, field)
    },

    getEpidemiologyIcon: function (patientRow){
      var palette = this.epidemiology_palette
      var field = palette.column
      return this.getEpidemiologyIconUrl(patientRow, palette, field)
    },

    getEpidemiologyIconUrl: function(patientRow, palette, field){
        var found
        if (palette.type=='qualitative'){
          lowerValue = patientRow[field].toLowerCase()
          //Remove accents
          lowerValue = accentsTidy(lowerValue)
          lowerValue = lowerValue.replace(' ','_')

          if (lowerValue in palette.images){
            return palette.images[lowerValue].img
          }
          else{
            return palette.images['indefinit'].img
          }
        }
        // else{
        //   rangs = palette.rangs
        //   value = parseFloat(patientRow[field])
        //   found=null
        //   rangs.forEach(function(rang, ind, arr){
        //     if ((value >= rang.minValue) && (value <= rang.maxValue) ){
        //       found = rang.image
        //     }
        //   })
        //   return found;
        // }
    },

    epidemiologyMarkerInMap: function(val, year, month, s_d, e_d){
       validDate = val[this.epidemiology_palette_date]
       if (validDate===null){
         validDate = val.date_notification
       }
       var markerDate = moment(validDate)
       var isValid = false;
       var str=''
        if (s_d && e_d) {
          var startDate = s_d
          var endDate = e_d
          isValid = ( (markerDate >= startDate) && (markerDate <= endDate) )
        }
        else{
            //some months
            if (month) {
              if (month.indexOf((1+markerDate.month()))!==-1){
                  //and some years
                  if (year) {
                    if (year.indexOf(markerDate.year())!==-1){
                      //month OK , year OK
                      isValid = true
                    }
                  }
                  //this month all years
                  else{
                      isValid = true
                  }
                }
            }
            else{
                //all months, some years
                if (year) {
                  if (year.indexOf(markerDate.year())!==-1){
                    isValid = true
                  }
                }
                else{
                  isValid = true;
                }
            }
        }
      return isValid;
    },

    epidemiology_filter: function() {
        var dict = {"indefinit":"undefined",
                   "probable": "likely",
                   "sospitos": "suspected",
                   "confirmat": "confirmed-not-specified",
                   "confirmat_den": "confirmed-den",
                   "confirmat_chk": "confirmed-chk",
                   "confirmat_zk": "confirmed-zk",
                   "confirmat_yf": "confirmed-yf",
                   "confirmat_wnv": "confirmed-wnv",
                   'no_cas': 'nocase'
                 }

        if (!'epidemiology_data' in this || typeof this.epidemiology_data === 'undefined') return;
        _this = this
        var start_date = 0, end_date = 0, years = 0, months = 0;

        //Get time filters from MAP
        if (this.filters.daterange && typeof this.filters.daterange !== 'undefined') {
          start_date = moment(this.filters.daterange.start);
          end_date = moment(this.filters.daterange.end);
        } else {
          if(this.filters.years.length !== 0){
              years = this.filters.years;
          }

          if(this.filters.months.length !== 0){
              months = this.filters.months;
          }
        }

        this.epidemiology_layer.clearLayers();

        this.epidemiology_data.forEach(function(val, index, arr){
            //if date NOT in range jump to next
            if (_this.epidemiologyMarkerInMap(val,years, months, start_date, end_date)){
                  var key = accentsTidy(val.patient_state)
                  key = key.replace(' ', '_').toLowerCase();
                  var selected_states = $('select[name=epidemiology-state]').val()

                  if (selected_states.indexOf(dict[key])!==-1
                      || selected_states.indexOf('all')!==-1) {
                          //get icon style
                          iconImage = _this.getEpidemiologyIcon(val)
                          var epiMarker = L.marker([val['lat'], val['lon']],
                               {icon: new _this.epiIcon(
                                 {iconUrl: iconImage})
                               })
                          epiMarker._data = val
                          epiMarker._data.marker_type='epidemiology'
                          epiMarker.properties = val
                          epiMarker.on('click',function(e){
                                _this.show_epidemiology_report(e)
                          })
                          _this.epidemiology_layer.addLayer(epiMarker)
                        }
                }
        })

        this.epidemiology_layer.addTo(this.map);
        this.putEpidemiologyLegend()
    },

    addEpidemiologyLayer: function(){
      _this = this;

      //Icon properties
      $.ajax({
          type: "GET",
          url: MOSQUITO.config.URL_API + 'epi/data/', // + _this.dateParamsToString(),
          dataType: 'json',
          cache: true,
          success: function (response) {
              _this.epidemiology_data = response.rows;
              if ('epidemiology_data' in _this &&
                  typeof _this.epidemiology_data !== 'undefined')
                  _this.epidemiology_filter()

              if (response.rows.length==0){
                alert(t('epidemiology.empty-layer'))
                _this.map.removeLayer(_this.epidemiology_layer)
              }
          }
      });
    },

    loadForecastVectorModel: function() {
      let year = $('#yearVectorMunicipalityProb').val();
      if (typeof year === 'undefined') {
        year = new Date().toISOString().slice(0, 4)
      }

      let month = $('#monthVectorMunicipalityProb').val();
      var date = year + '/' + month;
      let layerpos = this.getLayerPositionFromKey('M');
      let layer = MOSQUITO.config.layers[layerpos];
      let ranges = layer.prob_ranges;

      $.ajax({
        'url': URL_MODELS_VECTOR_GRID + date,
        'context': this,
        'complete': function(resp) {
          let all_data = resp.responseJSON;
          let prob = all_data.prob;
          let sd = all_data.sd;
          //remove virus layer if exists
          if (this.munis_virus_prob_layer) {
              this.map.removeLayer(this.munis_virus_prob_layer);
          }
          // PROBABILTY
          var probabilities = new L.geoJson(prob, {
            'style': function(feature) {
              let range = this.getForecastRange(layer.prob_ranges, feature.properties.prob);
              return {
                  fillColor: range.color,
                  color: range.color,
                  fillOpacity: 0.7,
                  opacity:0.1,
                  stroke:true,
                  weight: 5
              }
            }
          }).addTo(map);
          // STANDRARD DEVIATION
          stroke = {'14':0, '19':1}
          MOSQUITO.app.mapView.layers.standard_deviation = new L.geoJson(sd, {
            pointToLayer: function (feature, latlng) {
              let range = this.getForecastRange(layer.sd_ranges, feature.properties.val);
              //Get dots radius size
              var y = map.getSize().y,
                  x = map.getSize().x;
              // calculate the distance the one side of the map to the other using the haversine formula
              var maxMeters = map.containerPointToLatLng([0, y]).distanceTo( map.containerPointToLatLng([x,y]));
              // calculate how many meters each pixel represents
              var metresPerPixel = maxMeters/x;
              radius = 1000 / metresPerPixel
              return L.circle(latlng, 1000, {
                  fillColor: range.color,
                  color: '#000',
                  fillOpacity: 0.7,
                  opacity: 0.7,
                  stroke: true,
                  weight: 1,
                  radius: radius
              });
            }
          }).addTo(map);
        }
      })
    }
    ,
    loadForecastModel: function() {
      var forecast_zeroPoint ={"type": "Point", "coordinates": [0,0]};

      this.tileIndex = geojsonvt(forecast_zeroPoint , this.userFixtileOptions);
      this.forecast_layer_prob = L.canvasTiles()
          .params({ debug: false, padding: 0 })
          .drawing(this.prob_drawingOnCanvas);

      this.forecast_layer_sd = L.canvasOverlay()
        .params({'data': forecast_zeroPoint})
        .drawing(this.sd_drawingOnCanvas);

      this.forecast_layer = L.layerGroup([this.forecast_layer_prob, this.forecast_layer_sd]);
      // this.forecast_layer.addTo(this.map);
    }
    ,
    refreshForecastModel: function() {
      var layer_key = 'M'
      let year = $('#yearVectorMunicipalityProb').val();
      let vector = $('#selectVectorId').val();
      if (typeof year === 'undefined') {
        year = new Date().toISOString().slice(0, 4)
      }
      let month = $('#monthVectorMunicipalityProb').val();
      month = ("00"+month).slice (-2)
      this.map.removeLayer(this.forecast_layer);
      var file_name = MOSQUITO.config.MODELS_FILE_NAME;

      $.ajax({
        // 'url': MOSQUITO.config.URL_API + 'get/prediction/grid/' + year + '/' + month,
        'url': MOSQUITO.config.URL_MODELS_VECTOR_GRID + vector + '/' + year + '/' + month +'/'+file_name,
        cache: true,
        context: this,
        success: function(resp) {
          let all_data = resp;
          var sd_flag = true;
          var geojson = this.geoJsonFromCsv(all_data, sd_flag, layer_key)
          //remove vector/virus layer if exists
          if (this.munis_virus_prob_layer) {
              this.map.removeLayer(this.munis_virus_prob_layer);
          }
          // PROBABILTY
          MOSQUITO.app.tileIndex = geojsonvt(geojson.prob, this.userFixtileOptions);
          // STANDRARD DEVIATION
          this.grid_sd_data = geojson.sd
          this.forecast_layer_sd.params({'data':this.grid_sd_data});

          // RELOAD
          this.map.addLayer(this.forecast_layer);
        }
      })
    }
    ,
    prob_drawingOnCanvas: function(canvasOverlay, params) {
      let tileIndex = MOSQUITO.app.tileIndex;
      var ctx = params.canvas.getContext('2d');
      ctx.globalCompositeOperation = 'source-over';

      if (!tileIndex){
        return;
      }
      let layerpos = MOSQUITO.app.mapView.getLayerPositionFromKey('M');
      let layer = MOSQUITO.config.layers[layerpos];
      var bounds = params.bounds;
      params.tilePoint.z = params.zoom;

      var tile = tileIndex.getTile(params.tilePoint.z, params.tilePoint.x, params.tilePoint.y);
      if (!tile) {
        return;
      }

      ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);
      var features = tile.features;

      for (var i = 0; i < features.length; i++) {
        var feature = features[i],
            type = feature.type;

        if (typeof feature.tags.color === 'undefined') {
          let range = _this.getForecastRange(layer.prob_ranges, feature.tags.prob);
          feature.tags.color = range.color;
        }

        ctx.fillStyle = feature.tags.color;
        ctx.strokeStyle = feature.tags.color;

        ctx.beginPath();

        for (var j = 0; j < feature.geometry.length; j++) {
            var geom = feature.geometry[j];

            for (var k = 0; k < geom.length; k++) {
                var p = geom[k];
                var extent = 4096;
                var x = p[0] / extent * 256;
                var y = p[1] / extent * 256;
                if (k) ctx.lineTo(x  + params.options.padding, y   + params.options.padding);
                else ctx.moveTo(x  + params.options.padding, y  + params.options.padding);
            }
        }
        if (type === 3 || type === 1) ctx.fill('evenodd');
        ctx.stroke();
      }
    }
    ,
    sd_drawingOnCanvas: function(canvasOverlay, params) {
      var ctx = params.canvas.getContext('2d');
      ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);
      isDeviationVisible = (map.getZoom() > MOSQUITO.config.deviation_min_zoom)

      if (!isDeviationVisible) return true;

      let tileIndex = MOSQUITO.app.tileIndex;
      if (!tileIndex){
        return;
      }
      let layerpos = MOSQUITO.app.mapView.getLayerPositionFromKey('M');
      let layer = MOSQUITO.config.layers[layerpos];

      //Get dots radius size
      var y = map.getSize().y,
          x = map.getSize().x;
      // calculate the distance the one side of the map to the other using the haversine formula
      var maxMeters = map.containerPointToLatLng([0, y]).distanceTo( map.containerPointToLatLng([x,y]));
      // calculate how many meters each pixel represents
      var metresPerPixel = maxMeters/x;

      radius = 1000 / metresPerPixel
      if (radius > MOSQUITO.config.max_sd_radius){
        radius = MOSQUITO.config.max_sd_radius
      }

      ctx.strokeStyle = 'rgba(0,0,0,0.5)';
      ctx.lineWidth   = 1;

      data = _this.grid_sd_data
      for (var i = 0; i < data.features.length; i+=1) {
        if (typeof data.features[i].properties.color === 'undefined') {
          let range = _this.getForecastRange(layer.sd_ranges, data.features[i].properties.val);
          data.features[i].properties.color = range.color;
        }
        ctx.fillStyle = data.features[i].properties.color;
        var d = data.features[i].geometry.coordinates;
        dot = canvasOverlay._map.latLngToContainerPoint([d[1], d[0]]);
        ctx.beginPath();
        ctx.arc(dot.x, dot.y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.closePath();
      }
    }
    ,
    getForecastRange: function(ranges, val) {
      let result = ranges.filter(function(range) {
        return range.minValue <= val && range.maxValue > val;
      })[0];
      if (typeof result == 'undefined') {
        if (val <= ranges[0].minValue)
          result = {'color': ranges[0].color}
        if (val >= ranges[ranges.length - 1].maxValue)
          result = {'color': ranges[ranges.length - 1].color};
      }
      return result;
    }
    ,
    addDrainStormLayer: function() {
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
            url = MOSQUITO.config.URL_API + 'stormdrain/data/';
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

            });
        }
        //otherwise
        else{
          _this.drainstorm_layer.addTo(_this.map);
        }

    }
    ,
    checkStormDrainInfo:function(){
    }
    ,
    colorizeGridFeatures: function(arr) {
        _this = this;
        layer = this.LAYERS_CONF[this.getLayerPositionFromKey('F')];
        arr.forEach(function(item){
            pos = (item.properties.num_fixes.toString().length > 4)?3:item.properties.num_fixes.toString().length - 1;
            item.properties.color = 'rgba('+ layer.segments[pos].color+' , '+ layer.segments[pos].opacity +')';
        });
        return true;
    }
    ,
    addCoverageLayer: function(layer) {
        _this = this;
        var strokecolor = this.LAYERS_CONF[layer].style.strokecolor
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
            ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);
            var features = tile.features;
            //ctx.strokeStyle = 'grey';

            for (var i = 0; i < features.length; i++) {
                var feature = features[i],
                    type = feature.type;

                ctx.fillStyle = (feature.tags && feature.tags.color)? feature.tags.color : strokecolor;
                //ctx.strokeStyle = strokecolor;
                ctx.strokeStyle = ctx.fillStyle;
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
        };

        var zeroPoint ={"type": "Point",
            "coordinates": [0,0]};

        _this.userfixtileIndex = geojsonvt(zeroPoint , _this.userFixtileOptions);
        _this.coverage_layer = L.canvasTiles()
            .params({ debug: false, padding: 5 })
            .drawing(drawingOnCanvas);

        //_this.coverage_layer.addTo(_this.map);
    },

    refreshCoverageLayer: function() {
        layerLI = $('label[i18n="layer.userfixes"]').parent();
        if (typeof MOSQUITO.app.mapView !== 'undefined') MOSQUITO.app.mapView.loading.on(layerLI);
        _this = this;
        year = this.filters.years;
        if (year.length === 0) year = 'all';
        months = (this.filters.months.length>0)?this.filters.months:'all';
        if ('daterange' in this.filters && typeof this.filters.daterange !== 'undefined' && this.filters.daterange !== null) {
          daterange = this.filters.daterange;
          date_start = moment(daterange.start).format('YYYY-MM-DD');
          date_end = moment(daterange.end).format('YYYY-MM-DD');
        } else {
          date_start = 'N';
          date_end = 'N';
        }
        url = MOSQUITO.config.URL_API + 'userfixes/'+year+'/'+months+'/'+date_start+'/'+date_end;
        $.ajax({
            "method": 'GET',
            "async": true,
            "cache": true,
            "url": url
        }).done(function(data) {
          //if not logged then remove vector model layers
          if (!MOSQUITO.app.headerView.logged){
            if (_this.munis_vector_prob_layer) {
                _this.map.removeLayer(_this.munis_vector_prob_layer);
            }
          }
            _this.colorizeGridFeatures(data.features);
            _this.userfixtileIndex = geojsonvt(data, _this.userFixtileOptions);
            _this.map.removeLayer(_this.coverage_layer);
            _this.map.addLayer(_this.coverage_layer);
            //_this.coverage_layer.redraw();
        });
    },

    fetch_data: function(zoom, bbox, callback){
        var url = '';
        bbox = this.shortenBbox(bbox);

        //check notification & hashtag filters
        hashtag_value = this.getHashtagValue();

        //check municipalities filter
        municipalities_value = this.getMunicipalitiesValue();

        //Daterange
        daterange_value = this.getDaterangeValue();

        //Notif and notiftypes
        notif_value =  this.getNotifValue();
        notiftypes_value = this.getNotifTypesValue();

        if (
            daterange_value.toUpperCase() !== 'N/N'  ||
            hashtag_value.toUpperCase() !== 'N'  ||
            municipalities_value !== 'N'  ||
            notif_value.toUpperCase() !== 'N'  ||
            notiftypes_value !== 'N'
          ) {
            url = MOSQUITO.config.URL_API +
                'observations/' + bbox + '/' + daterange_value + '/' +
                hashtag_value +'/'+ municipalities_value +'/'+notif_value +'/' +
                notiftypes_value;
          }

        else{
            url = MOSQUITO.config.URL_API + 'observations/' +
                  zoom + '/' + bbox;
        }
        $.ajax({
            method: 'GET',
            url: url
        })
        .done(function(resp) {
            callback(resp);
        })
        .fail(function(error) {
            if (console && console.error) {
              console.log('AJAX ERROR !!! '+error)
            }
        });
    },

    fetch_item: function(id, callback){
        var item;

        if(item !== undefined){
            callback(item._data);
        }else{

            $.ajax({
                method: 'GET',
                url: MOSQUITO.config.URL_API + 'observations/' + id
            })
            .done(function(resp) {
                callback(resp);
            })
            .fail(function(error) {
                if (console && console.error) console.error(error);
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

        this.map.on('zoomend',function(){
            vectorModelLayer = _this.getLayerPositionFromKey('M');
            virusModelLayer = _this.getLayerPositionFromKey('N');

            if (vectorModelLayer ==-1 && virusModelLayer ==-1 ) return true

            minDevZoom = MOSQUITO.config.deviation_min_zoom
            if (map.getZoom() <= minDevZoom){
              $('ul.forecast_sd').css('opacity', '.3');
            }
            else {
              $('ul.forecast_sd').css('opacity', '1');
            }
        });

        this.map.on('movestart',function(){
            var bbox = _this.map.getBounds().toBBoxString();
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

            for(var i = 0; i < item.c; i++){
                pos = new L.LatLng(item.lat, item.lon);
                marker = _this.getMarkerType(pos, item.category);
                if (marker) {
                  marker._data = item;
                  marker._data.marker_type='observation';
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
    ,
    shortenBbox: function (bbox){
      var longBbox = bbox.split(',');
      var shortBbox = longBbox.map(function(x) {
         return (parseFloat(x).toFixed(4));
      });
      return shortBbox.toString();
    },

    getDaterangeValue: function(){
      var value = 'N/N';

      if ( 'daterange' in this.filters && this.filters.daterange !== null) {
        start = moment(this.filters.daterange.start).format('YYYY-MM-DD');
        end = moment(this.filters.daterange.end).format('YYYY-MM-DD');
        value = start + '/' + end;
        if (value === '/') value='N/N';
      }
      return value;
    },

    getMunicipalitiesValue: function(){
      var value  = 'N';
      if (MOSQUITO.app.headerView.logged){
        if ($('#municipalities-checkbox').prop('checked')){
          value = '0';
          return value;
        }
      }

      if ( 'municipalities' in this.filters && this.filters.municipalities.length>0 ) {
        value=this.filters.municipalities;
      }
      else{
        value = 'N';
      }

      return value;
    },

    getNotifValue: function(){
      var value = 'N'
      if ( ('notif' in this.filters && this.filters.notif !== false )  ) {
        value = this.filters.notif.toString();
      }
      return value;
    },

    getNotifTypesValue: function(){
      var value = 'N'
      if ( 'notif_types' in this.filters && this.filters.notif_types !== null ) {
        value = this.filters.notif_types;
      }
      return value;
    },

    getHashtagValue: function(){
      var value = 'N'
      if ( 'hashtag' in this.filters && typeof this.filters.hashtag !== 'undefined' && this.filters.hashtag.trim()!='') {
        //replace '#'' for ':' so  django can accept the url
        value = this.filters.hashtag.replace('#',':')
        value = value.replace(/ /g, ",");
        if (value =='') value='N';
      }
      else value='N';
      return value;
    }

});
