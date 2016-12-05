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

        getLayerPosition: function(lyr){
            var layer, ret = null;
            for(var i in this.options.layers){
                layer = this.options.layers[i].layer;
                if(layer._meta.key === lyr._meta.key){
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
                item = _this.container.find('.layers > ul > li:nth-child(' + (p+1) + ')');
                if (layer.layer._meta.key == 'F' && 'mapView' in MOSQUITO.app && 'coverage_layer' in MOSQUITO.app.mapView) {
                  MOSQUITO.app.mapView.coverage_layer._meta = layer.layer._meta;
                  layer.layer = MOSQUITO.app.mapView.coverage_layer;
                }
                if (_this._map.hasLayer(layer.layer)) {
                    item.addClass('active');
                }else{
                    item.removeClass('active');
                }
            });
        },

        getContent: function() {
            var _this = this;
            this.container = $('<div>').attr('class', 'sidebar-control-layers');

            var closeButton = this.getCloseButton().appendTo(this.container);

            var section = $('<div>').attr('class', 'section layers');

            section.appendTo(this.container);

            var list = $('<ul id="map_layers_list">').appendTo(section);

            if (MOSQUITO.app.headerView.logged) var layers = MOSQUITO.config.logged.layers;
            else var layers = MOSQUITO.config.layers || this.options.layers;

            $.each(layers, function(i, layer) {
      				  var item = $('<li>').attr('class', 'list-group-item').appendTo(list);
                switch (layer.key) {
                    case 'E':
                        //Different types of breeding sites
                        $('<label i18n="'+layer.title+'" class="multiclass">').appendTo(item);
                        var sublist = $('<ul>').attr('class', 'sub-sites').appendTo(item);
                        for (var cat in layer.categories) {
                          var subitem = $('<li>').attr('class', 'sublist-group-item').appendTo(sublist);
                          $('<img>').attr('src', 'img/marker_'+cat+'.svg').attr('class', 'icon').appendTo(subitem);
                          $('<label i18n="map.'+cat+'">').appendTo(subitem);
                        }
                    break;
                    case 'F':
                        $('<label i18n="'+layer.title+'" class="multiclass">').appendTo(item);
                        var sublist = $('<ul>').attr('class', 'sub-sites').appendTo(item);
                        // get the segments for the legend
                        for (i=0;i<layer.segments.length;++i) {
                            var subitem = $('<li>').attr('class', 'sublist-group-item').appendTo(sublist);
                            // category image
                            var color = (layer.segmentationkey == 'color') ? layer.segments[i].color : layer.style.fillColor;
                            var opacity = (layer.segmentationkey == 'opacity') ? layer.segments[i].opacity : layer.style.fillOpacity;
                            $('<div>')
                              .css('width', 20)
                              .css('height', 20)
                              .css('background',color)
                              .css('border', '1px solid orange')
                              .css('float', 'left')
                              .css('margin-right', '10px')
                              .css('opacity', opacity)
                              .appendTo(subitem);
                            // category label
                            if (!('to' in layer.segments[i])) label = '>= '+layer.segments[i].from;
                            else if (!('from' in layer.segments[i]) || layer.segments[i].from == 0) label = '<= '+layer.segments[i].to;
                            else label = layer.segments[i].from+' - '+layer.segments[i].to;
                            $('<label>').html(label).appendTo(subitem);
                        }
                    break;
                    default:
                        $('<img>').attr('src', layer.icon).attr('class', 'icon').appendTo(item);
                        $('<label i18n="'+layer.title+'">').appendTo(item);
                    break;
                }

        		item.on('click', function() {
                    if (layer.key == 'F') {
                        MOSQUITO.app.mapView.coverage_layer._meta = {
                          'key': 'F',
                          'icon': "img/marker_userfixes.svg",
                          'title': "layer.userfixes",
                          'layer': MOSQUITO.app.mapView.coverage_layer
                        };
                        theLayer = MOSQUITO.app.mapView.coverage_layer;
                    } else {
                        theLayer = layer.layer;
                    }

                    if (_this._map.hasLayer(theLayer)) {
                        _this._map.removeLayer(theLayer);
                    } else {
                        _this._map.addLayer(theLayer);
                    }
                    _this._map.fire('layerchange', {
                        layer : theLayer
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
