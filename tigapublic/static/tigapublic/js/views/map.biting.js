var MapView = MapView.extend({

    LAYERS_CONF: MOSQUITO.config.layers,
    show_bitting_sd: MOSQUITO.config.show_bitting_sd,
    highlight_layer: undefined,
    biting_tileIndex:undefined,
    sd_municipalities_data: undefined,
    vector_first_time_loading: true, //by default
    virus_first_time_loading: true,
    sd_data:undefined,

    addBitingLayer: function(layer) {
        _this = this;
        var strokecolor = this.LAYERS_CONF[layer].color_border_prob

        var zeroPoint ={"type": "Point",
            "coordinates": [0,0]};

        _this.userfixtileIndex = geojsonvt(zeroPoint , _this.userFixtileOptions);

        // _this.biting_layer = L.canvasTiles()
        //     .params({ debug: false, padding: 5 })
        //     .drawing(probOnCanvas);

        _this.bites_prob = L.canvasTiles()
                              .params({ debug: false, padding: 0 })
                              .drawing(_this.probOnCanvas);

        this.bites_sd = L.canvasOverlay()
                              .params({ debug: false, padding: 0 })
                              .drawing(_this.sdOnCanvas);

        _this.biting_layer = L.layerGroup([_this.bites_prob, _this.bites_sd]);
    }
    ,
    probOnCanvas: function(canvasOverlay, params) {
        //Get ranges and color_border_sd
        var bounds = params.bounds;
        var pad = 0;
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
        ctx.strokeStyle = 'grey';

        for (var i = 0; i < features.length; i++) {
            var feature = features[i],
                type = feature.type;

            ctx.fillStyle = (feature.tags && feature.tags.color)? feature.tags.color : strokecolor;
            //ctx.strokeStyle = strokecolor;
            ctx.strokeStyle = ctx.fillStyle;
            ctx.beginPath();

            for (var j = 0; j < feature.geometry.length; j++) {
                var geom = feature.geometry[j];
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
    }
    ,
    sdOnCanvas: function(canvasOverlay, params) {
      var ctx = params.canvas.getContext('2d');


      ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);
      isDeviationVisible = (map.getZoom() > MOSQUITO.config.deviation_min_zoom)

      if (!isDeviationVisible) return true;
      if (_this.sd_data===undefined) return true;

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

      data = _this.sd_data
      for (var i = 0; i < data.features.length; i+=1) {
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
    requiredCSVColumns: function (headers, validator) {
      var required = validator.required;
      for (var a=0; a<required.length; a++){
        var field = required[a];
        if (headers.indexOf(field)==-1) return false;
      }
      return true;
    },
    geoJsonFromCsv: function (data, sd_flag, key){
        var gridSize = MOSQUITO.config.gridSize;
        var raws = data.split(/\r?\n/)
        var headers = raws.shift().split(',');
        var lon_pos = headers.indexOf('lon')
        var lat_pos = headers.indexOf('lat')
        var prob_pos = headers.indexOf('prob_u95')

        if (sd_flag){
          var sd_pos = headers.indexOf('sd')
          var sd_geojson = {
            "type": "FeatureCollection",
            "features": []
          }

        }
        //check if csv format ok OK
        var validator ={
          'required': ['lon', 'lat', 'prob_u95']
        }
        if (!this.requiredCSVColumns(headers, validator)) {
          alert('Data file format error')
          item = $('#layer_R')
          MOSQUITO.app.mapView.loading.off(item);
          return {};//returns an empty dict
        }

        var polygon_geojson = {
          "type": "FeatureCollection",
          "features": []
        }
        var layer_conf = this.LAYERS_CONF[this.getLayerPositionFromKey(key)];
        var ranges = layer_conf.prob_ranges
        if (sd_flag){
          var ranges_sd = layer_conf.sd_ranges
        }

       for (var a = 0; a < raws.length; a++){
         var raw = raws[a].split(',');
         var min_lon = parseFloat(raw[lon_pos])
         var min_lat = parseFloat(raw[lat_pos])
         if (isNaN(min_lon) || isNaN(min_lat)) continue;
         var max_lon = min_lon + gridSize
         var max_lat = min_lat + gridSize

         //get color for each cell grid
         var prob_value = parseFloat(raw[prob_pos])
         var color_prob=''

         if (prob_value<=ranges[0].maxValue) color_prob = ranges[0].color;
         else if (prob_value<=ranges[1].maxValue) color_prob = ranges[1].color;
         else if (prob_value<=ranges[2].maxValue) color_prob = ranges[2].color;
         else color_prob = ranges[3].color;

         var polygon = {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [
            [
              [min_lon, min_lat], [min_lon, max_lat],
              [max_lon, max_lat], [max_lon, min_lat],
              [min_lon, min_lat]
              ]
            ]}, "properties": {
             'v': prob_value,
             'color': color_prob,
             'sd': parseFloat(raw[sd_pos])
            }
          }
          if (sd_flag){
            var color_sd=''
            sd_value = parseFloat(raw[prob_pos])
            if (sd_value<=ranges_sd[0].maxValue) color_sd = ranges_sd[0].color;
            else if (sd_value<=ranges_sd[1].maxValue) color_sd = ranges_sd[1].color;
            else if (sd_value<=ranges_sd[2].maxValue) color_sd = ranges_sd[2].color;
            else color_sd = ranges_sd[3].color;

            var point = {"type": "Feature", "geometry": {"type": "Point", "coordinates":
                 [min_lon +(gridSize/2), min_lat+(gridSize/2)]
               }, "properties": {
                'v': sd_value,
                'color': color_sd,
                'sd': parseFloat(raw[sd_pos])
               }
             }
          }

        polygon_geojson.features.push(polygon)
        if (sd_flag){
          sd_geojson.features.push(point)
        }
       }

       if (sd_flag){
         return {'prob': polygon_geojson, 'sd': sd_geojson};
       }
       else{
         return {'prob': polygon_geojson};
       }

    }
    ,
    refreshBitingLayer: function() {
        var layer_key = 'R'
        layerLI = $('li#layer_R')
        if (typeof MOSQUITO.app.mapView !== 'undefined') MOSQUITO.app.mapView.loading.on(layerLI);
        _this = this;

        year = $('#yearBitingLayer').val();
        month = $('#monthBitingLayer').val();
        //2 digits for month value
        month = ('0' + month).slice(-2);

        url = MOSQUITO.config.URL_MODELS_BITING + year+'/'+month+'/'+ MOSQUITO.config.MODELS_FILE_NAME;
        $.ajax({
          "method": 'GET',
          "async": true,
          "cache": true,
          "url": url
        }).done(function(data) {
          var geojson = _this.geoJsonFromCsv(data, _this.show_bitting_sd, layer_key)
          if (_this.show_bitting_sd){
            _this.sd_data = geojson.sd;
          }
          //if geojson is valid
          if (Object.keys(geojson.prob).length > 0) {
            _this.userfixtileIndex = geojsonvt(geojson.prob, _this.userFixtileOptions);
            //remove exclusive model layers
            if (_this.munis_vector_prob_layer){
              _this.map.removeLayer(_this.munis_vector_prob_layer);
            }
            if (_this.munis_virus_prob_layer){
              _this.map.removeLayer(_this.munis_virus_prob_layer);
            }

            if (_this.forecast_layer){
              _this.map.removeLayer(_this.forecast_layer);
            }
            //now add layer
            _this.map.removeLayer(_this.biting_layer);
            _this.map.addLayer(_this.biting_layer);
          }else{
            //remove layer
            _this.map.removeLayer(_this.biting_layer);
          }
        });
    }
});
