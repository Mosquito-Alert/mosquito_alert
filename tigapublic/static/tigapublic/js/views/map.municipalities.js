var MapView = MapView.extend({

    LAYERS_CONF: MOSQUITO.config.layers,
    munisDict:undefined,
    munisGeom:undefined,
    highlight_layer: undefined,
    prob_tileIndex:undefined,
    sd_municipalities_data: undefined,
    vector_first_time_loading: true, //by default
    virus_first_time_loading: true,
    munis_border_color:undefined,
    ////////////////////
    //COMMON FUNCTIONS
    ////////////////////

    //Add dict the properties of each feature (color, etc)
    colorizeFeatures: function (municipalitiesData) {
        var dict = _this.munisDict
        var data = municipalitiesData
        var counter = 0;
        for (var i = 0; i < data.features.length; i++) {
         if ('codigoine' in data.features[i].properties){
           if (data.features[i].properties.codigoine in dict){
             data.features[i].properties.prob = dict[data.features[i].properties.codigoine].prob;
             data.features[i].properties.sd = dict[data.features[i].properties.codigoine].sd;
             if (data.features[i].properties.tipus==2){
               data.features[i].properties.color = dict[data.features[i].properties.codigoine].sd_color;
             }
             else{
               data.features[i].properties.color = dict[data.features[i].properties.codigoine].color;
             }
           }
           else{
             //when municipality not in dict
             data.features[i].properties.color = 'rgba(255,0,0,0)';
           }
         }
         else{
           //when no codigoine
           data.features[i].properties.color = 'rgba(255,0,0,0)';
         }

        counter += data.features[i].geometry.coordinates[0].length;
      }
        return counter;
    }
    ,
    // returns municipalities dict
    processMunicipalitiesData: function (allText, layerKey) {
        var aLayer = MOSQUITO.config.layers[_this.getLayerPositionFromKey(layerKey)]
        _this.munis_border_color = aLayer.color_border_prob;
        var prob_colors=[], sd_colors=[]
        var prob_maxRanges=[], sd_maxRanges=[]
        for(var a=0; a<aLayer.prob_ranges.length;a++){
          prob_colors.push(aLayer.prob_ranges[a].color)
          prob_maxRanges.push(aLayer.prob_ranges[a].maxValue)
        }
        for(var a=0; a<aLayer.sd_ranges.length;a++){
          sd_colors.push(aLayer.sd_ranges[a].color)
          sd_maxRanges.push(aLayer.sd_ranges[a].maxValue)
        }

        var record_num = 6;  // or however many elements there are in each row
        var allTextLines = allText.split(/\r?\n/)
        var entries = allTextLines[0].split(',');
        var lines = [];
        dict ={}
        var prob_color, sd_color, n;
        //check headers first: month,PROVMUN,prob_l95,prob_median,prob_u95,sd
        // var aLine = allTextLines[0].replace('"','').split(',')
        var aLine = allTextLines[0].toLowerCase().split(',')
        var month_pos = aLine.indexOf('month')
        var provmun_pos = aLine.indexOf('provmun')
        var prob_l95_pos = aLine.indexOf('prob_l95')
        var prob_median_pos = aLine.indexOf('prob_median')
        var prob_u95_pos = aLine.indexOf('prob_u95')
        var sd_pos = aLine.indexOf('sd')

        if (
            provmun_pos ===-1 ||
            prob_l95_pos ===-1 ||
            prob_median_pos === -1 ||
            prob_u95_pos === -1
          ){
            alert('Data format error')
            item = $('#layer_'+layerKey)
            MOSQUITO.app.mapView.loading.off(item);
            dict['status'] = 'error';
          }
        else{
          for (var a=1; a<allTextLines.length; a++) {
            aLine = allTextLines[a].split(',')
              //Probability range
              if (aLine[prob_u95_pos]!='' && aLine[sd_pos]!='') {
                var prob_value = parseFloat(aLine[prob_u95_pos])

                if (prob_value<=prob_maxRanges[0]) n=0
                else if (prob_value<=prob_maxRanges[1]) n=1
                else if (prob_value<=prob_maxRanges[2]) n=2
                else n=3

                prob_color=prob_colors[n]

                //Uncertainty range
                sd_value = parseFloat(aLine[sd_pos])

                if (sd_value<=sd_maxRanges[0]) n=0
                else if (sd_value<=sd_maxRanges[1]) n=1
                else if (sd_value<=sd_maxRanges[2]) n=2
                else n=3

                sd_color=sd_colors[n]
                dict[aLine[provmun_pos]]={
                  'color': prob_color,
                  'sd_color': sd_color,
                  'prob': prob_value,
                  'sd': sd_value
                }
              }
          }
          dict['status'] = 'success';
        }

        return dict
    }
    ,
    munisDrawing: function (canvasOverlay, params) {
          var pad=0
          var ratio=5
          var bounds = params.bounds;
          params.tilePoint.z = params.zoom;

          var ctx = params.canvas.getContext('2d');
          ctx.globalCompositeOperation = 'source-over';

          var tile = _this.prob_tileIndex.getTile(params.tilePoint.z, params.tilePoint.x, params.tilePoint.y);
          if (!tile) {
              // tile empty
              return;
          }

          ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);
          var features = tile.features;
          ctx.strokeStyle = _this.munis_border_color;

          for (var i = 0; i < features.length; i++) {
              var feature = features[i],
                  type = feature.type;

              ctx.fillStyle = feature.tags.color ? feature.tags.color : 'rgba(255,0,0,0.05)';
              if ((feature.tags.tipus==2) && (feature.tags.color=='rgba(255,0,0,0)')) continue;
              minZoom = MOSQUITO.config.deviation_min_zoom
              if ((feature.tags.tipus==2) && (params.zoom<=minZoom)) continue;
              ctx.beginPath();

              for (var j = 0; j < feature.geometry.length; j++) {

                  var geom = feature.geometry[j];

                  if (type === 1) {
                      ctx.arc(geom[0] * ratio + pad, geom[1] * ratio + pad, 2, 0, 2 * Math.PI, false);
                      continue;
                  }

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
    ////////////////////
    // VECTOR FUNCTIONS
    ////////////////////

    loadVectorProbMunisModel: function() {
      var vector_zeroPoint ={"type": "Point", "coordinates": [0,0]};
      this.prob_tileIndex = geojsonvt(vector_zeroPoint , this.userFixtileOptions);

      this.munis_geometries = L.canvasTiles()
                                .params({ debug: false, padding: 0 })
                                .drawing(this.munisDrawing);

      this.munis_vector_centroids = L.canvasOverlay()
                                .params({ debug: false, padding: 0 })
                                .drawing(this.sd_DrawingOnCanvas);

      this.munis_vector_prob_layer = L.layerGroup([this.munis_geometries, this.munis_vector_centroids]);
      // this.munis_vector_prob_layer.addTo(this.map);

      //if logged prepare also the grid layer
      if (MOSQUITO.app.headerView.logged){
        this.loadForecastModel()
      }
    }
    ,
    sd_DrawingOnCanvas: function(canvasOverlay, params) {
      var ctx = params.canvas.getContext('2d');
      var dict = _this.munisDict

      ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);
      isDeviationVisible = (map.getZoom() > MOSQUITO.config.deviation_min_zoom)

      if (!isDeviationVisible) return true;
      if (_this.sd_municipalities_data===undefined) return true;

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

      data = _this.sd_municipalities_data
      for (var i = 0; i < data.features.length; i+=1) {
        if (typeof dict[data.features[i].properties.codigoine] !== 'undefined') {
          thisMuni = dict[data.features[i].properties.codigoine]
          ctx.fillStyle = thisMuni.sd_color;
          var d = data.features[i].geometry.coordinates;
          dot = canvasOverlay._map.latLngToContainerPoint([d[1], d[0]]);
          ctx.beginPath();
          ctx.arc(dot.x, dot.y, radius, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
          ctx.closePath();
        }
      }
    }
    ,
    refreshVectorProbMunisModel: function() {
      _this = this
      var thisSelect = 'selectRegionVectorModel'

      function loadVectorMunicipalities(data_model, data_geoms, data_sd_geoms){
         //if not logged remove coverage_layer
         if (!MOSQUITO.app.headerView.logged){
           if (_this.coverage_layer) {
               _this.map.removeLayer(_this.coverage_layer);
           }
         }

          _this.colorizeFeatures(data_geoms)
          var tileOptions = {
              maxZoom: 20,  tolerance: 5, extent: 4096, buffer: 64,
              debug: 0,     indexMaxZoom: 0, indexMaxPoints: 100000
          };
          //removing virus layer is required because shares geometries with vector layer
          if (_this.munis_virus_prob_layer) {
              _this.map.removeLayer(_this.munis_virus_prob_layer);
              //This caused a crash
              //_this.map.removeLayer(_this.biting_layer);
          }

          _this.prob_tileIndex = geojsonvt(data_geoms, tileOptions);
          _this.sd_municipalities_data = data_sd_geoms
          _this.munis_vector_prob_layer.addTo(_this.map);

          //fitbounds only if select Region has changed
          if ($('#'+thisSelect).data('prev')!==$('#'+thisSelect).val()){
            _this.map.fitBounds(L.geoJson(data_geoms).getBounds());
            $('#'+thisSelect).data('prev', $('#'+thisSelect).val())
          }
          if (_this.vector_first_time_loading){
            $('#'+thisSelect).data('prev', $('#'+thisSelect).val())
            _this.vector_first_time_loading = false
          }
      }

      //remove biting layers
      if (_this.biting_layer){
        _this.map.removeLayer(_this.biting_layer);
      }

      //Get type radio if looged
      if (MOSQUITO.app.headerView.logged){
        var modelType = $("input[name='modelType']:checked").val();
        if (modelType=='grid') {
          _this.map.removeLayer(MOSQUITO.app.mapView.munis_vector_prob_layer);
          _this.refreshForecastModel()
          return
        }
        else{
          _this.map.removeLayer(MOSQUITO.app.mapView.forecast_layer);
        }
      }
      //when not logged show only grid layer and exit
      else{
        _this.refreshForecastModel()
        return
      }

      var modelType = 'municipalities';

      let year = $('#yearVectorMunicipalityProb').val();
      if (typeof year === 'undefined') {
        year = new Date().toISOString().slice(0, 4)
      }
      let month = $('#monthVectorMunicipalityProb').val();
      let region = $('#selectRegionVectorModel').val();
      this.map.removeLayer(this.munis_vector_prob_layer);

      let vector = $('#selectVectorId').val();
      var file_name = MOSQUITO.config.MODELS_FILE_NAME;
      url_data = MOSQUITO.config.URL_MODELS_VECTOR_MUNICIPALITIES + vector + '/' + year + '/' + ("00"+month).slice (-2) + '/'+file_name

      /*url_munis_geoms = MOSQUITO.config.URL_API + 'static/geoms/ccaa/ccaa_' + region + '.js'
      url_sd_geoms = MOSQUITO.config.URL_API + 'static/geoms/ccaa/ccaa_sd_' + region + '.js'*/
      url_munis_geoms = '/static/tigapublic/geoms/ccaa/ccaa_' + region + '.js'
      url_sd_geoms = '/static/tigapublic/geoms/ccaa/ccaa_sd_' + region + '.js'

      var j1 = $.ajax( {
          type: "GET",
          url: url_data,
          dataType: "text"
      })

      var j2 = $.ajax({
          type: "GET",
          url: url_munis_geoms,
          'dataType': 'json'
      })

      var j3 = $.ajax({
          type: "GET",
          url: url_sd_geoms,
          'dataType': 'json'
      })

      $.when(j1, j2, j3).then(function(data_model, data_geoms, data_sd_geoms){
        layerKey='M'
        _this.munisDict = _this.processMunicipalitiesData(data_model[0],layerKey)
        _this.munisGeom = data_geoms[0]
        _this.munisSdGeom = data_sd_geoms[0]

        var circleRadius = 1000
        var circleStyle = {
            stroke: false,
            color:'black',
            weigth: 0,
            opacity:1,
            fillOpacity:1
        }

        if (_this.munisDict.status=='success'){
          loadVectorMunicipalities(_this.munisDict, _this.munisGeom, _this.munisSdGeom)
        }
      })
    }
    ,
    ////////////////////
    // VIRUS  FUNCTIONS
    ////////////////////

    loadVirusProbMunisModel: function() {
      var virus_zeroPoint ={"type": "Point", "coordinates": [0,0]};
      this.prob_tileIndex = geojsonvt(virus_zeroPoint , this.userFixtileOptions);
      this.munis_geometries = L.canvasTiles()
                                .params({ debug: false, padding: 0 })
                                .drawing(this.munisDrawing);

      this.munis_virus_centroids = L.canvasOverlay()
                                .params({ debug: false, padding: 0 })
                                .drawing(this.sd_DrawingOnCanvas);

      this.munis_virus_prob_layer = L.layerGroup([this.munis_geometries, this.munis_virus_centroids]);

      // this.munis_virus_prob_layer.addTo(this.map);

      //if logged prepare also the grid layer
      if (MOSQUITO.app.headerView.logged){
        this.loadForecastModel()
      }
    }
    ,
    refreshVirusProbMunisModel: function() {
      _this = this
      var thisSelect = 'selectRegionVirusModel'
      function loadVirusMunicipalities(data_model, data_geoms, data_sd_geoms){
          _this.colorizeFeatures(data_geoms)
          var tileOptions = {
              maxZoom: 20,  tolerance: 5, extent: 4096, buffer: 64,
              debug: 0,     indexMaxZoom: 0, indexMaxPoints: 100000
          };

          _this.map.removeLayer(_this.munis_vector_prob_layer);
          //Removed this because it crashed the layer
          //_this.map.removeLayer(_this.biting_layer);

          _this.prob_tileIndex = geojsonvt(data_geoms, tileOptions);
          _this.sd_municipalities_data = data_sd_geoms
          _this.munis_virus_prob_layer.addTo(_this.map);

          if ($('#'+thisSelect).data('prev')!==$('#'+thisSelect).val()){
            _this.map.fitBounds(L.geoJson(data_geoms).getBounds());
            $('#'+thisSelect).data('prev', $('#'+thisSelect).val())
          }

          if (_this.virus_first_time_loading){
            $('#'+thisSelect).data('prev', $('#'+thisSelect).val())
            _this.virus_first_time_loading = false
          }
      }

      let year = $('#yearVirusMunicipalityProb').val();
      if (typeof year === 'undefined') {
        year = new Date().toISOString().slice(0, 4)
      }
      let month = $('#monthVirusMunicipalityProb').val();
      let region = $('#selectRegionVirusModel').val();
      let virus = $('#selectVirusId').val();

      if (this.munis_virus_prob_layer){
        this.map.removeLayer(this.munis_virus_prob_layer);
      }

      if (this.forecast_layer){
        this.map.removeLayer(this.forecast_layer);
      }

      var file_name = MOSQUITO.config.MODELS_FILE_NAME;
      url_data = MOSQUITO.config.URL_MODELS_VIRUS_MUNICIPALITIES + virus + '/' + year + '/' + ("00"+month).slice (-2) + '/'+ file_name

      /*url_munis_geoms = MOSQUITO.config.URL_API + 'static/geoms/ccaa/ccaa_' + region + '.js'
      url_sd_geoms = MOSQUITO.config.URL_API + 'static/geoms/ccaa/ccaa_sd_' + region + '.js'*/
      url_munis_geoms = '/static/tigapublic/geoms/ccaa/ccaa_' + region + '.js'
      url_sd_geoms = '/static/tigapublic/geoms/ccaa/ccaa_sd_' + region + '.js'

      var j1 = $.ajax( {
          type: "GET",
          url: url_data,
          dataType: "text"
      })

      var j2 = $.ajax({
          type: "GET",
          url: url_munis_geoms,
          'dataType': 'json'
      })

      var j3 = $.ajax({
          type: "GET",
          url: url_sd_geoms,
          'dataType': 'json'
      })

      $.when(j1, j2, j3).then(function(data_model, data_geoms, data_sd_geoms){
        layerKey='N'
        _this.munisDict = _this.processMunicipalitiesData(data_model[0],layerKey)
        _this.munisGeom = data_geoms[0]
        _this.munisSdGeom = data_sd_geoms[0]

        var circleRadius = 1000
        var circleStyle = {
            stroke: false,
            color:'black',
            weigth: 0,
            opacity:1,
            fillOpacity:1
        }

        if (_this.munisDict.status=='success'){
          loadVirusMunicipalities(_this.munisDict, _this.munisGeom, _this.munisSdGeom)
        }
      })
    }
});
