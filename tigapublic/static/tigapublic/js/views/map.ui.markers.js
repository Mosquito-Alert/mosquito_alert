var MapView = MapView.extend({

    iconstype: {},
    epiIcon: L.Icon.extend({
        options: {
          iconSize:    [28, 28],
          iconAnchor:  [14, 14],
        }
    }),

    epiSelectedIcon: L.Icon.extend({
        options: {
          iconSize:    [38, 38],
          iconAnchor:  [18, 18],
        }
    }),

    getLayerKey: function(type) {

    },

    getIconUrlByKey: function(key){
        return 'img/marker_' + key.replace('#','_') + '.svg';
    },

    getIconUrlByIndex: function(i){
      // returns the icon belonging to the first category in the layer
      for (var cat in this.LAYERS_CONF[i].categories) {
        return 'img/marker_' + cat + '.svg';
      }
    },

    getIconUrl: function(type){
        icon = this.getLayerByMarkerCategory(type);
        if (icon) return 'img/marker_' + icon + '.svg';
        else {
          return false;
        }
    },

    getIconType: function(entire_type){
        var icon = this.getIconUrl(entire_type);
        if (icon) {
          if (!(entire_type in this.iconstype)){
              this.iconstype[entire_type] = new L.Icon({
                  iconUrl: icon,
                  iconSize:    [21, 28],
                  iconAnchor:  [10, 28],
                  iconSize:    [27, 35],
                  iconAnchor:  [13, 35],
                  //iconSize:    [36, 46],
                  popupAnchor: [1, -34]
              });
          }
          return _.clone(this.iconstype[entire_type]);
        } else return false;
    },

    getMarkerType: function(pos, type){
        icon = this.getIconType(type);
        if (icon) {
          var m = L.marker(pos, {"icon": icon});
          return m;
        } else return false;
    },

    markerUndoSelected: function(marker){
        var _this = this;
        if (marker._data.marker_type=='observation'){
          var marker = _.find(MOSQUITO.app.mapView.layers.layers.mcg.getLayers(), function(layer){
              if(layer._data.id === _this.scope.selectedMarker._data.id &&
                  _this.map.hasLayer(layer)
              ){
                  return layer;
              }
          });

          if(marker !== undefined){
              //_this.markerSetSelected(found);
              var type = marker._data.category;
              this.scope.selectedMarker = null;
              marker.setIcon(this.getIconType(type));
              if($(this.report_panel).is(':visible')){
                  this.controls.sidebar.closePane();
              }
          }
        }
        else{
          iconImgUrl = _this.getEpidemiologyIcon(marker._data)

          this.scope.selectedMarker = null;

          var selectedIcon = new this.epiIcon(
            {iconUrl: iconImgUrl})

          marker.setIcon(selectedIcon);
          if($(this.report_panel).is(':visible')){
              this.controls.sidebar.closePane();
          }
        }
    },

    markerSetSelected: function(marker){
        var _this = this;
        //observation marker
        if (marker._data.marker_type=='observation'){
          var type = marker._data.category;
          var iconUrl = this.getIconUrl(type);
          var ext = iconUrl.split('.').slice(-1)[0];
          iconUrl = iconUrl.replace('.' + ext, '_selected.' + ext);

          var selectedIcon = new L.Icon({
              iconUrl: iconUrl,
              iconSize:    [36, 46],
              iconAnchor:  [18, 46],
              popupAnchor: [1, -34]
          });
        }
        //epidemiology marker
        else{
          iconImgUrl = _this.getEpidemiologyIcon(marker._data).split('.').slice(0, -1).join('.')
          var selectedIcon = new this.epiSelectedIcon(
            {iconUrl: iconImgUrl +'_selected.svg'})
        }
        marker.setIcon(selectedIcon);
        marker._bringToFront();
    }

});
