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
    irideon_data_by_station: {},
    irideon_pulses_by_station: {},

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

        irideonLayer = this.getLayerPositionFromKey('Y');
        if (irideonLayer!==null) {
          // this.irideon_layer = L.layerGroup()
          this.irideon_layer = L.featureGroup()
        };

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

    addIrideonLayer: function(autozoom, callback){
      _this = this;
      if (typeof autozoom === 'undefined') autozoom = true;
      //Icon properties
      $.ajax({
          type: "GET",
          url: MOSQUITO.config.URL_API + 'irideon/data/', // + _this.dateParamsToString(),
          dataType: 'json',
          cache: true,
          success: function (response) {
              _this.irideon_data = response.rows;
              if ('irideon_data' in _this &&
                  typeof _this.irideon_data !== 'undefined')
                  _this.irideon_filter(autozoom)

              if (response.rows.length==0){
                // alert(t('epidemiology.empty-layer'))
                _this.map.removeLayer(_this.irideon_layer)
              }
              if (callback) {
                callback();
              }
          },
          error: function (e){
            item = $('#layer_Y')
            MOSQUITO.app.mapView.loading.off(item);
            _this.map.removeLayer(_this.irideon_layer)
          }
      });
    },

    irideon_filter: function(autozoom) {
      _this = this;
        if (!'irideon_data' in this || typeof this.irideon_data === 'undefined') {
          this.addIrideonLayer()
          return;
        }
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

        this.irideon_layer.clearLayers();
        var selected_species = $('#irideon_species').val()
        var selected_sex = $('#irideon_species_sex').val()
        // selected_species.push('pulse');

        //TO-DO count number of mosquitos shown in map (check species and date selections)
        var irideonLabels={}
        var estations={}
        if (selected_species!==null && selected_sex!==null){

          this.irideon_data.forEach(function(val, index, arr){
          //check if irideon data should show in map
          if (val.record_time!==null
                && selected_species.indexOf(val.spc)!==-1
                && selected_sex.indexOf(val.sex)!==-1
             ){

              let client_name = val.client_name;
              if (val.client_name.indexOf(' (') !== -1) {
                  //remove parenthesis content from client_name
                  client_name = val.client_name.substring(0, val.client_name.indexOf(' ('));
              }
              if (!(client_name in irideonLabels)){
                  irideonLabels[client_name] = 0;
                  estations[client_name]={'lat': val.lat, 'lon': val.lon}
                  _this.irideon_data_by_station[client_name] = [];
              }

              if (_this.irideonDataPassesFilters(val, years, months, start_date, end_date)){
                  //update counter
                  irideonLabels[client_name] = irideonLabels[client_name] + 1;
                  _this.irideon_data_by_station[client_name].push(val);
              }
          } else {
            if (_this.irideonDataPassesFilters(val, years, months, start_date, end_date)){
              let client_name = val.client_name;
              if (val.client_name.indexOf(' (') !== -1) {
                  //remove parenthesis content from client_name
                  client_name = val.client_name.substring(0, val.client_name.indexOf(' ('));
              }
              if (!(client_name in _this.irideon_pulses_by_station)) {
                  _this.irideon_pulses_by_station[client_name] = [];
              }
              _this.irideon_pulses_by_station[client_name].push(val);
            }
          }
        });

        this.irideon_stations = estations;
          this.drawIrideonMarkers(irideonLabels, estations, autozoom)
        }
    },

    drawIrideonMarkers: function(counters, estations, autozoom){
      var nradius = 10
      if (typeof autozoom === 'undefined') autozoom = true;
      function createClass(name,rules){
          var style = document.createElement('style');
          style.type = 'text/css';
          document.getElementsByTagName('head')[0].appendChild(style);
          if(!(style.sheet||{}).insertRule)
              (style.styleSheet || style.sheet).addRule(name, rules);
          else
              style.sheet.insertRule(name+"{"+rules+"}",0);
      }
      var color = this.LAYERS_CONF[this.getLayerPositionFromKey('Y')].iconColor;
      createClass('.irideon-marker::after',"border-top-color: " + color + ";");
      for (var key in estations) {
          var val = estations[key]
          var digits = counters[key].toString().length
          var icon = L.divIcon({
                  className: 'custom-div-icon',
                  html: "<div class=\"irideon-marker irideon-size-" + digits + "\" style='background-color:"+color+";'><div class=\"title\">"+ key + "</div><div>"+counters[key]+"</div></div>",
              });

          const marker = L.marker([val.lat, val.lon], { icon: icon, station: key });

          marker.on('click', function(event) {
            if(this.trap_panel.is(':visible') === false){
                this.controls.sidebar.togglePane(this.trap_panel, $('<div>'));
            }

            // this.loading.show(this.map.latLngToContainerPoint(event.latlng));
            const station = event.target.options.station;
            if (event.originalEvent.ctrlKey) {
              let option = $('select#trap_stations option[name="' + station + '"]');
              if (option.attr('selected') === 'selected') {
                option.removeAttr('selected');
              } else {
                option.attr('selected', 'selected');
              }
              this.irideonShowReport($('select#trap_stations').val());
            } else {
              this.irideonShowReport([station]);
            }
            this.moveMarkerIfNecessary(marker);

          }.bind(this));
          marker.addTo(this.irideon_layer);
      }

      this.irideon_layer.addTo(this.map);
      // if (autozoom) this.map.fitBounds(this.irideon_layer.getBounds().pad(1));
    },

    irideonDataPassesFilters: function (val, years, months, start_date, end_date){
      var elementDate = moment(val.record_time)
      var passesFilters = false;
       if (start_date && end_date) {
         passesFilters = ( (elementDate >= start_date) && (elementDate <= end_date) )
       }
       else{
           //some months
           if (months) {
             if (months.indexOf((1+elementDate.month()))!==-1){
                 //and some years
                 if (years) {
                   if (years.indexOf(elementDate.year())!==-1){
                     //month OK , year OK
                     passesFilters = true
                   }
                 }
                 //this month all years
                 else{
                     passesFilters = true
                 }
               }
           }
           else{
               //all months, some years
               if (years) {
                 if (years.indexOf(elementDate.year())!==-1){
                   passesFilters = true
                 }
               }
               else{
                 passesFilters = true;
               }
           }
       }
      return passesFilters;
    },

    isDayInFilter: function(day) {
      var time_windows = this.convertTimeFiltersToTimeWindows();
      if (time_windows.length === 0) return true;
      var exists = time_windows.find(function(item) {
        return (day.isSameOrAfter(moment(item[0])) && day.isSameOrBefore(moment(item[1])))
      });
      return typeof exists !== 'undefined';
    },

    convertTimeFiltersToTimeWindows: function() {
      var windows = [];
      if (this.filters.months.length !== 0) {
        var years = this.filters.years;
        // Si no hem indicat cap any, agafa'ls tots des del 2014.
        if (this.filters.years.length === 0) {
          years = [];
          year = 2014;
          while (year <= new Date().getFullYear()) {
            years.push(year);
            year = year + 1;
          }
        }
        years.forEach(function(year) {
          this.filters.months.forEach(function(month) {
            month = ('00'+month).slice(-2);
             var start = year + '/' + month + '/01';
             var end = moment(start).endOf('month').format('YYYY/MM/DD');
            windows.push([start, end]);
          });
        }.bind(this));
      }
      if (this.filters.daterange && typeof this.filters.daterange !== 'undefined') {
        windows.push([this.filters.daterange.start.format('YYYY/MM/DD'),
                      this.filters.daterange.end.format('YYYY/MM/DD')]);
      }
      return windows;
    },

    irideonAggregateStations: function(station, data, totals, labels) {
      if (typeof this.irideon_data_by_station[station] === 'undefined' || this.irideon_data_by_station[station].length === 0) {
        return {'data': data, 'totals': totals, 'labels': labels};
      }
      var raw_data = this.irideon_data_by_station[station];
      var oldest = moment(raw_data[0].record_time);
      var pointer = 0;
      var today = moment();
      if (this.filters.daterange && typeof this.filters.daterange !== 'undefined') {
        oldest = moment(this.filters.daterange.start);
        today = moment(this.filters.daterange.end);
      }
      if (this.filters.months.length !== 0) {
        var today = moment();
        var months = this.filters.months;
        var years = this.filters.years;
        if (!years.length) {
          if (new Date().getMonth() < months[0])
          years = [new Date().getFullYear()];
        }
        var oldest = moment(years[0] + '/' + ("0"+months[0]).slice(-2) + '/01');
        if (oldest.isAfter(today)) {
          years[0] = years[0] - 1;
          oldest = moment(years[0] + '/' + ("0"+months[0]).slice(-2) + '/01');
        }
        var today = moment(years[years.length -1] + '/' + ("0"+months[months.length - 1]).slice(-2) + '/01').endOf('month');
      }
      while (oldest.isSameOrBefore(today)) {
        var initial = null;
        if (this.isDayInFilter(oldest)) {
          initial = 0;
        }
        // store the day with initial values of 0
        if (labels.indexOf(oldest.format('YYYY-MM-DD')) === -1) {
          labels.push(oldest.format('YYYY-MM-DD'));
          Object.keys(data).forEach(function(species){
            data[species].push(initial);
          });
        }
        // search the data for this day
        let day = moment(raw_data[pointer].record_time);
        while (day.format('YYYY-MM-DD') == oldest.format('YYYY-MM-DD')) {
          if (pointer < raw_data.length) {
            let record = raw_data[pointer];
            var index = labels.indexOf(moment(record.record_time).format('YYYY-MM-DD'));
            if (index !== -1) {
              if (record.sex === 'm') data[record.spc + '.male'][index] += 1;
              if (record.sex === 'f') data[record.spc + '.female'][index] += 1;
              totals[record.spc][record.sex] += 1;
            } else {
              console.error('no date found on data')
            }

          }
          ++pointer;
          if (pointer < raw_data.length) {
            day = moment(raw_data[pointer].record_time);
          } else {
            pointer = raw_data.length - 1;
            day = moment();
          }
        }
        oldest = oldest.add(1, 'day');
      }
      return {'data': data, 'totals': totals, 'labels': labels};
    },

    irideonAgregatePulses: function(station, trap_data, labels) {
      var raw_data = this.irideon_pulses_by_station[station];
      var oldest = moment(trap_data[1], 'YYYY-MM-DD');
      var pointer = 0;
      var data = [station];
      var today = moment(trap_data[trap_data.length - 1], 'YYYY-MM-DD');
      if (this.filters.daterange && typeof this.filters.daterange !== 'undefined') {
        oldest = moment(this.filters.daterange.start);
        today = moment(this.filters.daterange.end);
      }
      if (this.filters.months.length !== 0) {
        var today = moment();
        var months = this.filters.months;
        var years = this.filters.years;
        if (!years.length) {
          if (new Date().getMonth() < months[0])
          years = [new Date().getFullYear()];
        }
        var oldest = moment(years[0] + '/' + ("0"+months[0]).slice(-2) + '/01');
        if (oldest.isAfter(today)) {
          years[0] = years[0] - 1;
          oldest = moment(years[0] + '/' + ("0"+months[0]).slice(-2) + '/01');
        }
        var today = moment(years[years.length -1] + '/' + ("0"+months[months.length - 1]).slice(-2) + '/01').endOf('month');
      }
      while (oldest.isBefore(today, 'day') || oldest.isSame(today, 'day')) {
        var initial = null;
        if (this.isDayInFilter(oldest)) {
          initial = 0;
        }
        // store the day with initial values of 0
        if (labels.indexOf(oldest.format('YYYY-MM-DD')) === -1) {
          data[labels.length] = initial;
          labels.push(oldest.format('YYYY-MM-DD'));
        } else {
          var index = labels.indexOf(oldest.format('YYYY-MM-DD'));
          data[index] = initial;
        }

        // search the data for this day
        let day = moment(raw_data[pointer].record_time);
        while (day.isBefore(oldest, 'day')) {
          ++pointer;
          if (pointer < raw_data.length) {
            day = moment(raw_data[pointer].record_time);
          } else {
            pointer = raw_data.length - 1;
            day = moment().add(1, 'day');
          }
        }
        while (day.isSame(oldest, 'day')) {
          if (pointer < raw_data.length) {
            let record = raw_data[pointer];
            var index = labels.indexOf(day.format('YYYY-MM-DD'));
            if (index !== -1 && initial === 0) {
              data[index] += 1;
            } else {
              console.error(day.format('YYYY-MM-DD') + ' not found on data')
            }
          }
          ++pointer;
          if (pointer < raw_data.length) {
            day = moment(raw_data[pointer].record_time);
          } else {
            pointer = raw_data.length - 1;
            day = moment().add(1, 'day');
          }
        }
        oldest = oldest.add(1, 'day');
      }
      data = data.map(function(value) {
        if (typeof value === 'number') return Math.round((value / 48) * 100) / 100;
        else return value;
      });
      return {data: data, labels: labels};
    },

    irideonShowReport: function (stations) {
      if (!stations) stations = [];
      // highlight markers
      this.map.eachLayer( function(layer) {
        if(layer instanceof L.Marker) {
          if (typeof layer.options.station !== 'undefined') {
            if (stations.indexOf(layer.options.station) !== -1) {
              $(layer._icon).find('.irideon-marker').addClass('selected');
            } else {
              $(layer._icon).find('.irideon-marker').removeClass('selected');
            }
          }
        }
      });

      this.trap_panel.html('');
      a = new L.Control.SidebarButton();
      a.getCloseButton().appendTo(this.trap_panel);
      // prepare data
      var data = {};
      var pulses = [];
      var totals = {};
      var labels = ['x'];
      var labels_pulses = ['x'];
      $('#irideon_species').val().forEach(function (species) {
        data[species + '.male'] = [window.t('layer.' + species) + ' - ' + window.t('map.m-sex-label')];
        data[species + '.female'] = [window.t('layer.' + species) + ' - ' + window.t('map.f-sex-label')];
        totals[species] = {'m': 0, 'f': 0};
      });
      stations.forEach(function(station) {
        var count = this.irideonAggregateStations(station, data, totals, labels);
        data = count.data;
        totals = count.totals;
        labels = count.labels;
      }.bind(this));
      var new_labels = Object.assign([], labels);
      var label_label = new_labels.shift();
      new_labels = [label_label].concat(new_labels.sort());
      stations.forEach(function(station) {
        var pulses_aggregated = this.irideonAgregatePulses(station, new_labels, labels_pulses);
        pulses.push(pulses_aggregated.data);
        labels_pulses = pulses_aggregated.labels;
      }.bind(this));
      // Calculate absolute total
      var total = Object.keys(totals).reduce(function(acc, species){
        if (typeof acc === 'string') return totals[acc]['m'] + totals[acc]['f'] + totals[species]['m'] + totals[species]['f'];
        else {
          return acc + totals[species]['m'] + totals[species]['f'];
        }
      });
      if (typeof total === 'string') total = totals[total]['m'] + totals[total]['f'];
      // show the report
      if(!('content-trap-details' in this.templates)){
          this.templates[
              'content-trap-details'] = $('#content-trap-details-tpl').html();
      }
      var tpl = _.template(this.templates['content-trap-details']);
      //Get time filters from MAP
      var period = false;
      var month_names = [
        ['all', t('All months')],
        ['1', t('January')], ['2', t('February')], ['3', t('March')],
        ['4', t('April')], ['5', t('May')], ['6', t('June')],
        ['7', t('July')], ['8',t('August')], ['9', t('September')],
        ['10', t('October')], ['11', t('November')],
        ['12', t('December')]
      ];
      if (this.filters.daterange && typeof this.filters.daterange !== 'undefined') {
        start_date = moment(this.filters.daterange.start);
        end_date = moment(this.filters.daterange.end);
        period = start_date.format('DD-MM-YYYY') + ' <==> ' + end_date.format('DD-MM-YYYY')
      } else {
        period = ''
        if(this.filters.months.length !== 0){
            months = this.filters.months;
            period = months.map(function(month){return month_names[month][1]}).join(', ')
        }
        if(this.filters.years.length !== 0){
            years = this.filters.years;
            if (period !== '') period += ' <==> '
            period += years.join(', ')
        }
      }
      var all_stations = Object.keys(this.irideon_data_by_station);
      all_stations.sort();
      var show_total = $('#irideon_species').val().length > 1;
      var data_table = '<table>';
      // table header
      table_header = '<thead>';
      table_header += '<tr><th></th>';
      var species_header = $('#irideon_species').val().map(function(val){
        return '<th i18n="layer.' + val + '" class="center">' + val + '</th>';
      }).join('');
      table_header += species_header ;
      if (show_total) table_header += '<th i18n="map.total" class="center">Total</th>';
      table_header += '</tr></thead>';
      // body
      var table_body = '<tbody>';
      var total_by_species = [];
      var table_data = $('#irideon_species_sex').val().map(function(val) {
        var tr = '<tr><td i18n="map.' + val + '-sex-label" class="right">' + val + '</td>';
        var total_by_sex = 0;
        $('#irideon_species').val().forEach(function(item, idx) {
          total_by_sex += totals[item][val];
          if (typeof total_by_species[idx] === 'undefined') total_by_species[idx] = 0;
          total_by_species[idx] += totals[item][val];
          tr += '<td class="center">' + totals[item][val] + '</td>';
        });
        if (show_total) tr += '<th class="center">' + total_by_sex + '</th></tr>';
        return tr;
      }).join('');
      if ($('#irideon_species_sex').val().length > 1) {
        table_data += '<tr><th class="right" i18n="map.total">Total</th><th class="center">';
        table_data += total_by_species.join('</th><th class="center">');
        if (show_total) table_data += '</th><th class="center">' + total_by_species.reduce(function(a, b) {return a + b});
        table_data += '</th></tr>';
      }
      table_body += table_data + '</tbody>';
      data_table += table_header + table_body + '</table>';
      this.trap_panel.append(tpl({
        'trap_name': stations.join(', '),
        'data_table': data_table,
        'filter_date': period,
        'total': total,
        'stations': all_stations
      }));
      // select active stations on the station picker
      $('select#trap_stations option').each(function(idx, station) {
        let title = $(station).html();
        if (stations.indexOf(title) !== -1) {
          $(station).attr('selected', 'true');
        }
      });
      // Do all traps in view
      $('#traps_in_view').on('click', function(event) {
        var features = [];
        this.map.eachLayer( function(layer) {
          if(layer instanceof L.Marker) {
            if (typeof layer.options.station !== 'undefined') {
              if(map.getBounds().contains(layer.getLatLng())) {
                features.push(layer.options.station);
              }
            }
          }
        });
        this.irideonShowReport(features.sort());
      }.bind(this));
      var columns = [labels];
      Object.keys(data).forEach(function(species){
        columns.push(data[species]);
      });
      this.trap_chart_data = columns;
      var colors = {}
      colors[window.t('layer.tig')] = '#e10f21';
      colors[window.t('layer.tig') + ' - ' + window.t('map.m-sex-label')] = '#e10f21';
      colors[window.t('layer.tig') + ' - ' + window.t('map.f-sex-label')] = '#e10f21';
      colors[window.t('layer.cul')] = '#a24f96';
      colors[window.t('layer.cul') + ' - ' + window.t('map.m-sex-label')] = '#a24f96';
      colors[window.t('layer.cul') + ' - ' + window.t('map.f-sex-label')] = '#a24f96';
      colors[window.t('layer.zik')] = '#008c3a';
      colors[window.t('layer.zik') + ' - ' + window.t('map.m-sex-label')] = '#008c3a';
      colors[window.t('layer.zik') + ' - ' + window.t('map.f-sex-label')] = '#008c3a';

      var species = $('#irideon_species').val();
      var legend = true;
      if (species.length === 1) legend = false;

      this.trap_chart = c3.generate({
        bindto: '#traps-chart',
        size: {width: 460, height: 240},
        legend: { show: legend },
        data: {
          x: 'x',
          columns: [],
          colors: colors,
        },
        axis: {
            x: {
              label: {
                text: t('map.observation_date'),
                position: 'outer-center'
              },
              type: 'timeseries',
              tick: {
                  format: '%Y-%m-%d',
                  rotate: -30,
              }
            },
            y: {
              label: {
                text: t('layer.irideon.number'),
                position: 'outer-middle'
              }
            }
        },
      });
      var sex = $('#irideon_species_sex').val();
      if (sex.length === 1) {
        $('#trap-chart-filters').css('display', 'none');
      }
      else $('#trap-chart-filters').css('display', 'block');

      setTimeout(function() {
        this.irideonLoadChartData(sex);
      }.bind(this), 300);

      $('#trap-chart-filters input').on('click', function(event) {
        const selection = $(event.currentTarget).val();
        this.irideonLoadChartData(selection);
      }.bind(this));
      this.trap_uptime_chart_data = pulses;

      // add the mean values of each uptime serie
      var uptime_data = [];
      var colors = ['#191970', '#ffb6c1', '#ff0000', '#ffd700', '#00ff00', '#00ffff', '#ff00ff', '#006400'];
      var used_colors = {};
      pulses.forEach(function(serie, idx) {
        var total = serie.reduce(function(o, i) {
          if (typeof o === 'string') o = 0;
          return i + o;
        });
        var number = serie.reduce(function(a, b) {
          if (a !== null && b !== null) {
            if (typeof a === 'string') return 1;
            else return a + 1;
          } else {
            return a;
          }
        });
        var mean = Math.round(total/number * 100);
        serie[0] = serie[0] + ' (' + t('label.mean').toLowerCase() + ' = ' + (mean) + '%)';
        used_colors[serie[0]] = colors[idx];
      });

      this.uptime_trap_chart = c3.generate({
        bindto: '#traps-uptime-chart',
        size: {width: 460, height: 240},
        legend: { show: true },
        data: {
          x: 'x',
          columns: [labels_pulses].concat(pulses).concat(uptime_data),
          colors: used_colors,
        },
        axis: {
            x: {
              label: {
                text: t('map.observation_date'),
                position: 'outer-center'
              },
              type: 'timeseries',
              tick: {
                  format: '%Y-%m-%d',
                  rotate: -30,
              }
            },
            y: {
              label: {
                text: t('layer.irideon.uptime'),
                position: 'outer-middle'
              },
              max: 1,
              min: 0,
              padding: {top: 5, bottom: 5},
              tick:{
                  format: d3.format(',.0%')
              }
            }
        }
      });

      window.t().translate($('html').attr('lang'), this.trap_panel);
      $('select#trap_stations').selectpicker({liveSearch: true});
      $('select#trap_stations').on('hide.bs.select', function(event) {
        let selected_stations = $('select#trap_stations').val();
        this.irideonShowReport(selected_stations);
      }.bind(this));

      $('.trap-details .download').on('click', function(event) {
        // saveCSV(this.trap_chart_data);
        var metadata_file = this.LAYERS_CONF[this.getLayerPositionFromKey('Y')].metadata_file;
        $.ajax(metadata_file, {
          'complete': function(result) {
            var metadata = result.responseText;
            if (result.status !== 200) {
              metadata = t('map.trap-download-metadata');
            }
            saveTrapData(this.trap_chart_data.concat(this.trap_uptime_chart_data), metadata);
          }.bind(this)
        });
      }.bind(this));
      $('#add_trap_stations_button').on('click', function(event) {
        $('#add_trap_stations').toggleClass('visible');
        $('#trap-count').toggleClass('visible');
      });
    },

    irideonLoadChartData: function(filter) {
      var columns = [];
      if (typeof filter === 'undefined') filter = 'all';
      if (typeof filter === 'object') {
        if (filter.length === 2) filter = 'all';
        if (filter.length === 1) {
          if (filter[0] === 'm') filter = 'male';
          if (filter[0] === 'f') filter = 'female';
        }
      }
      if (filter === 'all' || true) {
        var title = false;
        var data_copy = $.extend(true, [], this.trap_chart_data);
        data_copy.forEach(function(serie, idx) {
          if (idx === 0) columns.push(serie);
          else {
            let label = serie[0];
            let sex = 'all';
            if (label.indexOf(' - ') !== -1) {
              sex = label.substring(label.indexOf(' - ') + 3);
              if (sex.trim() === window.t('map.m-sex-label')) sex = 'male';
              if (sex.trim() === window.t('map.f-sex-label')) sex = 'female';
              if (filter === 'all') {
                label = label.substring(0, label.indexOf(' - '));
              }
            }
            serie[0] = label;
            if (label !== title) {
              title = label;
              if (filter === 'all' || filter === sex) {
                columns.push(serie);
              }
            } else {
              serie.forEach(function(data, idx2) {
                if (idx2 !== 0) {
                  if (filter === 'all' || filter === sex) {
                    columns[columns.length - 1][idx2] = parseInt(columns[columns.length - 1][idx2]) + parseInt(data);
                  }
                }
              })
            }
          }
        });
      }
      this.trap_chart.load({
        columns: columns,
        unload: true,
      })
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
