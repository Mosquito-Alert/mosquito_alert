var MapView = MapView.extend({

    iconstype: {},

    getIconUrl: function(type){
        return 'img/marker_' + type + '.svg';
    },

    getIconType: function(entire_type){

        var validation = entire_type.split('#');
        var type = validation[0];
        if (validation[0] === 'site') {
            type = type + '_' + validation[1];
        }

        if (!(type in this.iconstype)){

            this.iconstype[type] = new L.Icon({
                iconUrl: this.getIconUrl(type),
                iconSize:    [21, 28],
                iconAnchor:  [10, 28],
                popupAnchor: [1, -34]
            });

        }
        return _.clone(this.iconstype[type]);
    },

    getMarkerType: function(pos, type){
        //var _this = this;
        var m = L.marker(pos, {icon: this.getIconType(type)});
        // m.on('click', function(){
        //     _this.scope.selectedMarker = this;
        // });
        return m;
    },

    markerUndoSelected: function(marker){
        if(marker !== undefined && marker !== null){
            var type = marker._data.simplified_expert_validation_result;
            marker.setIcon(this.getIconType(type));
            this.scope.selectedMarker = null;
            if($(this.report_panel).is(':visible')){
                this.controls.sidebar.closePane();
            }
        }
    },

    markerSetSelected: function(marker){
        var type = marker._data.simplified_expert_validation_result;
        //remove site#XXXX
        type = type.replace(/#(.*)$/i,'');
        var iconUrl = this.getIconUrl(type);
        var ext = iconUrl.split('.').slice(-1)[0];

        iconUrl = iconUrl.replace('.' + ext, '_selected.' + ext);

        var selectedIcon = new L.Icon({
            iconUrl: iconUrl,
            iconSize:    [21, 28],
            iconAnchor:  [10, 28],
            popupAnchor: [1, -34]
        });

        marker.setIcon(selectedIcon);
    }

});
