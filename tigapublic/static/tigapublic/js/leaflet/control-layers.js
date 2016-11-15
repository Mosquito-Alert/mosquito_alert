var MOSQUITO = (function (m) {

    var ControlLayers = L.Control.SidebarButton.extend({
        options: {
            style: 'leaflet-control-layers-btn',
            position: 'topleft',
            title: 'leaflet-control-layers-btn',
            text: '',
            active: false,
            layers: []
        },
        /*
        set_active_class: function(layer, item){

            if (this._map.hasLayer(layer)) {
                item.removeClass('active');
                this._map.removeLayer(layer);
            }else{
                item.addClass('active');
                this._map.addLayer(layer);
            }

        },
        */
        getLayerPosition: function(lyr){
            var layer, ret = null;
            for(var i in this.options.layers){
                layer = this.options.layers[i].layer;
                if(layer === lyr){
                    ret = parseInt(i);
                    break;
                }
            }
            return ret;
        },

        setActiveClass: function(){
            var _this = this;
            var p, item;
            $.each(this.options.layers, function(i, layer) {
                p = _this.getLayerPosition(layer.layer);
                item = _this.container.find('ul > li:nth-child(' + (p+1) + ')');
                if (_this._map.hasLayer(layer.layer)) {
                    item.addClass('active');
                }else{
                    item.removeClass('active');
                }
            });
        },

        getContent: function(){
            var _this = this;
            this.container = $('<div>')
              .attr('class', 'sidebar-control-layers');

            var section = $('<div>')
              .attr('class', 'section layers');

            section.appendTo(this.container);

            var list = $('<ul>').appendTo(section);

            $.each(this.options.layers, function(i, layer) {

				var item = $('<li>')
					.attr('class', 'list-group-item')
					.appendTo(list);
                //item.data('_meta', layer);

				/*
                $('<img>')
					.attr('src', layer.icon)
					.attr('class', 'icon')
					.appendTo(item);

			    var label = $('<label i18n="'+layer.title+'">')
					.appendTo(item);

				label.append(t(layer.title));
                */

                if (layer.title != 'layer.site'){
					$('<img>')
						.attr('src', layer.icon)
						.attr('class', 'icon')
						.appendTo(item);
					var label = $('<label i18n="'+layer.title+'">')
                        .appendTo(item);
				}
				else{
                    //Different type of breeding sites
					var label = $('<label i18n="'+layer.title+'">')
	                    .appendTo(item);
					var sublist = $('<ul>')
                        .attr('class', 'sub-sites')
                        .appendTo(section);
                    //type 1
					var subitem = $('<li>')
                    	.attr('class', 'sublist-group-item')
	                    .appendTo(sublist);
					$('<img>')
                        .attr('src', 'img/marker_site_water.svg')
                        .attr('class', 'icon')
                        .appendTo(subitem);

					var label = $('<label i18n="map.sites_water">')
                        .appendTo(subitem);

                    //type 2
                    var subitem = $('<li>')
                    	.attr('class', 'sublist-group-item')
	                    .appendTo(sublist);
					$('<img>')
                        .attr('src', 'img/marker_site_dry.svg')
                        .attr('class', 'icon')
                        .appendTo(subitem);

					var label = $('<label i18n="map.sites_dry">')
                        .appendTo(subitem);

                    //type 3 ONLY REGISTERED users
                    /*
                    var subitem = $('<li>')
                    	.attr('class', 'sublist-group-item')
	                    .appendTo(sublist);
					$('<img>')
                        .attr('src', 'img/marker_site_other.svg')
                        .attr('class', 'icon')
                        .appendTo(subitem);

					var label = $('<label i18n="map.sites_other">')
                        .appendTo(subitem);
                        */
				}
			    //var label = $('<label i18n="'+layer.title+'">').appendTo(item);

				label.append(t(layer.title));

				item.on('click', function() {
                    if (_this._map.hasLayer(layer.layer)) {
                        _this._map.removeLayer(layer.layer);
                    }else{
                        _this._map.addLayer(layer.layer);
                    }
					_this._map.fire('layerchange', {
						layer : layer.layer
					});
				});

            });
            this.setActiveClass(section);
			this._map.on('layeradd', function(layer) {
				if('_meta' in layer.layer){
                    var p = _this.getLayerPosition(layer.layer);
                    var item = section.find('ul > li:nth-child(' + (p+1) + ')');
                    item.addClass('active');
                }
			});

            this._map.on('layerremove', function(layer) {
				if('_meta' in layer.layer){
                    var p = _this.getLayerPosition(layer.layer);
                    var item = section.find('ul > li:nth-child(' + (p+1) + ')');
                    item.removeClass('active');
                }
			});

            return this.container;

        },

        getSelectedKeys: function(){
            var _this = this;
            var keys = [];
            $.each(this.options.layers, function(i, layer) {
                if(_this._map && _this._map.hasLayer(layer.layer)){
                    keys.push(layer.key);
                }
            });
            return keys;
        }


    });

    m.control = m.control || {};
    m.control.ControlLayers = ControlLayers;

    return m;

}(MOSQUITO || {}));
