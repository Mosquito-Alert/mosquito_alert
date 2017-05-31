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
                item = _this.container.find('#layer_'+ layer.key) ;

                if (layer.layer._meta.key == 'F' && 'mapView' in MOSQUITO.app && 'coverage_layer' in MOSQUITO.app.mapView) {
                  MOSQUITO.app.mapView.coverage_layer._meta = layer.layer._meta;
                  layer.layer = MOSQUITO.app.mapView.coverage_layer;
                }
                if (_this._map.hasLayer(layer.layer)) {
                    item.addClass('active');
                    _this.container.find('#id' + layer.group).attr('aria-expanded','true');
                    _this.container.find('#div_' + layer.group).attr('aria-expanded','true');
                    _this.container.find('#div_' + layer.group).attr('class','collapse in');
                    item.parent().parent().prev().find('.layer-group').addClass('active');
                } else {
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

            var list = $('<div id="map_layers_list">').appendTo(section);

            //Get user groups
            if (MOSQUITO.app.headerView.logged) var Groups = MOSQUITO.config.logged.groups;
            else var Groups = MOSQUITO.config.groups || this.options.groups;

            //for each group, get all layers
            $.each(Groups, function(i, group) {

                if (MOSQUITO.app.headerView.logged) var layersAll = MOSQUITO.config.logged.layers;
                else var layersAll = MOSQUITO.config.layers || this.options.layers;

                layers = []; //get all layers for each group
                for (var a=0;  a <layersAll.length; a++){
                    layer = layersAll[a];
                    if (layersAll[a].group == group.name){
                        layers.push(layer)
                    }
                }
                //if group<>none

                if (group.name != 'none'){
                  //toggle button for one group
                  var toggleGrup = $('<div/>')
                      .attr('data-toggle','collapse')
                      .attr('data-target', '#div_'+group.name)
                      .attr('class','layer-group-trigger')
                      .attr('aria-expanded',"false")
                      .attr('id', 'id' + group.name)
                  .appendTo(list);

                  var parentDiv = $('<div/>')
                      .attr('class', 'layer-group list-group-item')
                  .appendTo(toggleGrup);

                  $('<div/>')
                     .attr('i18n', 'group.'+group.name)
                     .attr('class','group-title')
                 .appendTo(parentDiv)

                  //var icon = $('<i/>')
                  var icon = $('<div/>')
                      //.attr('class', group.icon)
                      .attr('class', 'layer-group-icon')
                      .attr('aria-hidden','true')
                  //.appendTo(parentDiv);

                  var divGroup = $('<div>')
                      .attr('id', 'div_'+group.name)
                      .attr('class', 'collapse') //+(!group.collapsed?'in':''))
                  .appendTo(list);

                }
                else{
                  var divGroup = $('<div>')
                      .attr('id', 'div_'+group.name)
                  .appendTo(list);
                }

                var ulGroup = $('<ul>').attr('id', 'ul_'+group.name).appendTo(divGroup);

                //Layers of each group
                $.each(layers, function(i, layer) {

                  classname = (group.name != 'none')?'list-group-item':'list-group-only-item';
          		    var item = $('<li>')
                        .attr('class', classname)
                        .attr('id', 'layer_'+layer.key)
                    .appendTo(ulGroup);

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
                                  .css('background','rgb('+color+')')
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
                        case 'Q': //DrainStorm
                            /*$('<img>').attr('src', layer.icon).attr('class', 'icon').appendTo(item);
                            $('<label i18n="'+layer.title+'">').appendTo(item);*/

                            div = $('<div class="icon-setup"></div>');
                            label = $('<label i18n="'+layer.title+'" class="multiclass">');
                            iconSetup = $('<i class="fa fa-cog storm_drain"></i>')
                            

                            div.appendTo(item)
                            iconSetup.appendTo(div);
                            label.appendTo(item);

                            $(iconSetup).on('click', function(e){
                                MOSQUITO.app.mapView.stormDrainSetup();
                                e.stopPropagation();
                                e.preventDefault();
                            })
                            
                            //Only for loggend and manager_group users
                            if (MOSQUITO.app.headerView.logged)
                            {
                              var isManager = false;
                              MOSQUITO.app.user.groups.some(function (v, i, arr){
                                if  (MOSQUITO.config.logged.managers_group.indexOf(v) !== -1) {
                                  isManager = true;
                                  return true;
                                }
                              })

                              if (isManager) {
                                iconUpload = $('<i class="fa fa-upload storm_drain"></i>')
                                iconUpload.appendTo(div);
                                $(iconUpload).on('click', function(e){
                                    MOSQUITO.app.mapView.stormDrainUploadSetup();
                                    e.stopPropagation();
                                    e.preventDefault();
                                })
                              }
                            }
                            
                            var sublist = $('<ul id="stormdrain_legend">').attr('class', 'sub-sites').appendTo(item);
                            /*
                            layer.categories.drainstorm.forEach(function (item, index) {
                              var subitem = $('<li>').attr('class', 'sublist-group-item').appendTo(sublist);
                              $('<img>').attr('src', 'img/marker_drainstorm_'+item+'.svg').attr('class', 'icon').appendTo(subitem);
                              $('<label i18n="drainstorm.'+item+'">').appendTo(subitem);
                            })*/
                        break;
                        default:
                            $('<img>').attr('src', layer.icon).attr('class', 'icon').appendTo(item);
                            $('<label i18n="'+layer.title+'">').appendTo(item);
                        break;
                    }

            		item.on('click', function() {

                        if (layer.key == 'F') {
                            //MOSQUITO.app.mapView.refreshCoverageLayer();
                            MOSQUITO.app.mapView.coverage_layer._meta = {
                              'key': 'F',
                              'icon': "img/marker_userfixes.svg",
                              'layer': MOSQUITO.app.mapView.coverage_layer
                            };
                            theLayer = MOSQUITO.app.mapView.coverage_layer;

                        } else if (layer.key == 'Q') {
                            /*if (!_this._map.hasLayer(MOSQUITO.app.mapView.drainstorm_layer)) {
                                MOSQUITO.app.mapView.loadStormDrainData();
                            }*/
                            MOSQUITO.app.mapView.drainstorm_layer._meta = {
                              'key': 'Q',
                              'icon': "img/marker_userfixes.svg",
                              'layer': MOSQUITO.app.mapView.drainstorm_layer
                            };
                            theLayer = MOSQUITO.app.mapView.drainstorm_layer;
                        }
                        else {
                            theLayer = layer.layer;
                        }

                        if ($('#layer_'+layer.key).hasClass('active')){
                            _this._map.removeLayer(theLayer);
                            if (layer.key=='Q') {
                              console.log('off for storm drain click');
                              _this._map.off('click', MOSQUITO.app.mapView.checkStormDrainInfo);
                            }
                        }
                         else {
                            layerLI = $('label[i18n="'+layer.title+'"]').parent();
                            MOSQUITO.app.mapView.loading.on(layerLI);
                            if (layer.key=='F') MOSQUITO.app.mapView.refreshCoverageLayer();
                            else if (layer.key=='Q') MOSQUITO.app.mapView.loadStormDrainData();
                            else _this._map.addLayer(theLayer, function() {alert('eiva');});
                        }
                        _this._map.fire('layerchange', {
                            layer : theLayer
                        });
                        // deactivate the parent menu
                        if (ulGroup.find('.active').length == 0) divGroup.prev().find('.layer-group').removeClass('active');
            		});
                });//end first each
            }); //end second each

            this.setActiveClass(section);

    		    this._map.on('layeradd', function(layer) {
              if('_meta' in layer.layer){
                var item = section.find('#layer_'+ layer.layer._meta.key) ;
                item.addClass('active');
                item.parent().parent().prev().find('.layer-group').addClass('active');
                MOSQUITO.app.mapView.loading.off(item);
              }
      			});

            this._map.on('layerremove', function(layer) {
              if('_meta' in layer.layer){
                var item = section.find('#layer_'+ layer.layer._meta.key);
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
