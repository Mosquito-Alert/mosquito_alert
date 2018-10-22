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
                if (layer.layer._meta.key == 'I' && 'mapView' in MOSQUITO.app && 'forecast_layer' in MOSQUITO.app.mapView) {
                  MOSQUITO.app.mapView.forecast_layer._meta = layer.layer._meta;
                  layer.layer = MOSQUITO.app.mapView.forecast_layer;
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

                //check user types
                if (MOSQUITO.app.headerView.logged)
                  {
                    var isManager = false;
                    var isSuperUser = false;
                    MOSQUITO.app.user.groups.some(function (v, i, arr){
                      if  (MOSQUITO.config.logged.managers_group.indexOf(v) !== -1) {
                        isManager = true;
                      }
                      if  (MOSQUITO.config.logged.superusers_group.indexOf(v) !== -1) {
                        isSuperUser = true;
                      }
                    })
                  }

                if (group.name != 'none') {
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

                //Iterate all layers of one group
                $.each(layers, function(i, layer) {
                  //Some layers have conditions to be shown
                  if (layer.key=='Q' && (!isManager && !isSuperUser)){
                    return true
                  }
                  //only when models available
                  if (layer.key=='I' && !MOSQUITO.config.predictionmodels_available.length) {
                    return true
                  }

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
                      case 'F': // user fixes
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
                                .css('border', '1px solid '+layer.style.strokecolor)
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
                      case 'I': // Forecast models
                          // TITLE
                          $('<label i18n="'+layer.title+'" class="multiclass">').appendTo(item);

                          // QUESTION MARK
                          let question_mark = $('<a>', {
                            'href':'#',
                            'data-toggle':'popover',
                            'data-placement':'left',
                            'i18n': 'layer.predictionmodels.description|data-content',
                            'data-container': 'body',
                            'class':'fa fa-question question-mark-toc'
                          })

                          question_mark.appendTo(item)
                          question_mark.on('click', function(event) {
                            // event.preventDefault();
                            event.stopPropagation();
                          });
                          $(question_mark).popover({
                            html: true,
                            content: function() {
                              return true;
                              }
                          });
                          // LISTEN ANY CLICK TO HIDE POPOVER
                          $(document).click(function(e) {
                            var isVisible = $("[data-toggle='popover']").data('bs.popover').tip().hasClass('in');
                            if (isVisible){
                              question_mark.click()
                            }
                          });
                          // DATE SELECTOR
                          var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                                        'August', 'September', 'October', 'November', 'December'];
                          // YEAR
                          var date_selector = $('<div>', {'id': 'forecast_date_selector'})
                            .appendTo(item);
                          $('<div>', {'i18n': 'general.year'}).css('padding', '5px')
                            .css('width', 40)
                            .appendTo(date_selector);
                          var first_time_loading = true;
                          var this_month = new Date().getMonth();
                          var year_select = $('<select>', {
                              'name': 'forecast_year',
                              'id': 'forecast_year',
                              'class': 'selectpicker dropup'})
                            .appendTo(date_selector)
                            .on('change', function(e) {
                              let year = $(this).val();
                              let found = false;
                              let i = 0;
                              let months_availability = [];
                              while (i < MOSQUITO.config.predictionmodels_available.length && !found) {
                                if (MOSQUITO.config.predictionmodels_available[i][0] == year) {
                                  found = true;
                                  months_availability = MOSQUITO.config.predictionmodels_available[i][1];
                                } else ++i;
                              }
                              previous_month = $(month_select).val() - 1
                              month_select.empty();
                              months.forEach(function(month, i) {
                                let attrs = {'value': i + 1, 'i18n': month};
                                if (months_availability[i] === 0) attrs['disabled'] = 'false';
                                month_select.append($('<option>', attrs));
                              });
                              t().translate(MOSQUITO.lng,month_select);

                              let option=''
                              if (first_time_loading) {
                                option = $('#forecast_month option')[this_month];
                              }
                              else{
                                option = $('#forecast_month option')[previous_month];
                              }
                              // if current month is disabled, check closest previous available month
                              if ($(option).is(':disabled')){
                                $(option).parent().find('option').not(':disabled')[0]
                              }else{
                                $(option).attr('selected', 'selected');
                              }

                              month_select.selectpicker('refresh');
                              first_time_loading = false;
                            });
                          $('<div>', {'style': 'clear:both'}).appendTo(item);
                          // MONTH
                          var date_selector = $('<div>', {'id': 'forecast_date_selector'})
                            .appendTo(item);
                          $('<div>', {'i18n': 'general.month'}).css('padding', '5px')
                              .css('width', 40)
                              .appendTo(date_selector);
                          var month_select = $('<select>', {
                              'name': 'forecast_month',
                              'id': 'forecast_month',
                              'class': 'selectpicker dropup'})
                            .appendTo(date_selector);
                          MOSQUITO.config.predictionmodels_available.forEach(function(y, i) {
                            let attrs = {'value': y[0]};
                            if (i === 0) attrs['selected'] = 'selected';
                            year_select.append($('<option>', attrs).html(y[0]));
                          });
                          setTimeout(function() {year_select.change()}, 100);
                          $('<div>', {'style': 'clear:both'}).appendTo(item);
                          // LEGEND PROBABILTY
                          var sublist = $('<ul>').attr('class', 'sub-sites').css('font-weight', 'bold').css('float', 'left').appendTo(item);
                          sublist.append($('<h5>', {'i18n': 'models.probability'}));
                          ind=0
                          this.prob_ranges.forEach(function(range) {
                            hover_label = 'models.hover-prob-label'+ind
                            var subitem = $('<li>')
                              .attr('i18n', hover_label+'|title')
                              .attr('class', 'sublist-group-item').appendTo(sublist);

                            $('<div>')
                              .css('width', 20)
                              .css('height', 20)
                              .css('background',range.color)
                              .css('border', '1px solid orange')
                              .css('float', 'left')
                              .css('margin-right', '10px')

                              .appendTo(subitem);
                            $('<label>', {'i18n': range.label}).appendTo(subitem);
                            ind = ind + 1
                          });
                          // LEGEND ST. DEV.
                          sublist = $('<ul>', {'class': 'sub-sites', 'id': 'forecast_sd'})
                            .css('font-weight', 'bold')
                            .css('float', 'left')
                            .appendTo(item);
                          sublist.append($('<h5>', {'i18n': 'models.uncertainty'}));
                          ind=0
                          this.sd_ranges.forEach(function(range) {
                            hover_label = 'models.hover-sd-label'+ind
                            var subitem = $('<li>')
                              .attr('i18n', hover_label+'|title')
                              .attr('class', 'sublist-group-item').appendTo(sublist);

                            $('<div>')
                              .css('width', 10)
                              .css('height', 10)
                              .css('background',range.color)
                              .css('border', '1px solid black')
                              .css('border-radius', '50%')
                              .css('float', 'left')
                              .css('margin-right', '10px')
                              .css('margin', '3px 10px 0 0px')
                              .appendTo(subitem);
                            $('<label>', {'i18n': range.label}).appendTo(subitem);
                            ind = ind + 1
                          });
                          if (map.getZoom() <= 7) {
                            sublist.css('opacity', '.3');
                          } else {
                            sublist.css('opacity', '1');
                          }
                      break;
                      case 'Q': //DrainStorm
                          //Only for loggend and manager_group users
                          if (MOSQUITO.app.headerView.logged)
                          {

                            if (isManager || isSuperUser){
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
                            }

                            if (isManager) {

                              iconUpload = $('<i class="fa fa-upload storm_drain"></i>')
                              iconUpload.appendTo(div);
                              $(iconUpload).on('click', function(e){
                                  MOSQUITO.app.mapView.stormDrainUploadSetup();
                                  e.stopPropagation();
                                  e.preventDefault();
                              })
                            }

                            var sublist = $('<ul id="stormdrain_legend">').attr('class', 'sub-sites').appendTo(item);
                          }

                      break;

                      case 'P': //Epidemilogy
                          isEpidemiologist_view = false
                          isEpidemiologist_edit = false

                          //Only for loggend and manager_group users
                          if (MOSQUITO.app.headerView.logged)
                          {
                            var isEpidemiologist = false;
                            MOSQUITO.app.user.groups.some(function (v, i, arr){
                              if  (MOSQUITO.config.logged.epidemiologist_view_group.indexOf(v) !== -1) {
                                isEpidemiologist_view = true;
                              }
                              if  (MOSQUITO.config.logged.epidemiologist_edit_group.indexOf(v) !== -1) {
                                isEpidemiologist_edit = true;
                              }
                            })
                          }
                          else{
                            return false
                          }

                          //only some groups can view this layer
                          if (!isEpidemiologist_view && !isEpidemiologist_edit && !isSuperUser) {
                            return false
                          }

                          div = $('<div class="icon-setup"></div>');
                          label = $('<label i18n="'+layer.title+'" class="multiclass">');
                          iconSetup = $('<i class="fa fa-cog epidemiology"></i>')

                          div.appendTo(item)
                          iconSetup.appendTo(div);

                          label.appendTo(item);

                          $(iconSetup).on('click', function(e){
                              MOSQUITO.app.mapView.epidemiologyFormSetup();
                              e.stopPropagation();
                              e.preventDefault();
                          })

                                //add listener to epidemiology filter
                          $('#select_epi-state').on('change', function(){
                              var pre = $(this).data('pre');
                              var newdata = $(this).val();
                              if (newdata===null){
                                  $(this).val(['all']);
                              }
                              else {
                                  if (pre.indexOf('all')!==-1 && newdata.indexOf('all')!==-1 ) {
                                    newdata.shift()
                                  }
                                  else if (pre.indexOf('all')===-1 && newdata.indexOf('all')!==-1 ) {
                                    newdata=['all']
                                  }
                                  $(this).val(newdata);
                              }

                              $(this).selectpicker('refresh');
                              $(this).data('pre', $(this).val());
                          });

                          if (isEpidemiologist_edit) {
                            iconUpload = $('<i class="fa fa-upload storm_drain"></i>')
                            iconUpload.appendTo(div);
                            $(iconUpload).on('click', function(e){
                                MOSQUITO.app.mapView.epidemiologyUploadSetup();
                                e.stopPropagation();
                                e.preventDefault();
                            })
                          }


                          var sublist = $('<ul id="epidemiolgy_legend">').attr('class', 'sub-sites').appendTo(item);

                      break;

                      default:
                          $('<img>').attr('src', layer.icon).attr('class', 'icon').appendTo(item);
                          $('<label i18n="'+layer.title+'">').appendTo(item);
                      break;
                  }

                //when click on a layer selector
                // console.log(MOSQUITO);
            		item.on('click', function(event) {
                  if (layer.key === 'I') {
                    MOSQUITO.app.mapView.forecast_layer._meta = {
                      'key': 'I',
                      'icon': "img/epi_confirmed.svg",
                      'layer': MOSQUITO.app.mapView.forecast_layer
                    };
                    theLayer = MOSQUITO.app.mapView.forecast_layer;
                    // When we unfold the select
                    var option = event.target;

                    if ($(option).hasClass('filter-option') ||
                          $(option).hasClass('caret') ||
                          $(option).hasClass('dropdown-toggle')) return;
                    // when we pick an option
                    // ... because we clicked on the span.text

                    if (option.tagName === 'A') option = event.target.children[0];
                  }
                  else if (layer.key === 'F') {
                      MOSQUITO.app.mapView.coverage_layer._meta = {
                        'key': 'F',
                        'icon': 'img/marker_userfixes.svg',
                        'layer': MOSQUITO.app.mapView.coverage_layer
                      };
                      theLayer = MOSQUITO.app.mapView.coverage_layer;

                  } else if (layer.key === 'Q') {
                      MOSQUITO.app.mapView.drainstorm_layer._meta = {
                        'key': 'Q',
                        'icon': "img/marker_userfixes.svg",
                        'layer': MOSQUITO.app.mapView.drainstorm_layer
                      };
                      theLayer = MOSQUITO.app.mapView.drainstorm_layer;
                  }
                  else if (layer.key == 'P') {
                      MOSQUITO.app.mapView.epidemiology_layer._meta = {
                        'key': 'P',
                        'icon': "img/epi_confirmed.svg",
                        'layer': MOSQUITO.app.mapView.epidemiology_layer
                      };
                      theLayer = MOSQUITO.app.mapView.epidemiology_layer;
                  }
                  else {
                      theLayer = layer.layer;
                  }

                  if ($('#layer_'+layer.key).hasClass('active')){
                    if ($(option).hasClass('text') && layer.key === 'I') {
                      MOSQUITO.app.mapView.refreshForecastModel();
                    } else {
                      _this._map.removeLayer(theLayer);
                      if (layer.key=='Q') {
                        _this._map.off('click', MOSQUITO.app.mapView.checkStormDrainInfo);
                      }
                    }
                  }
                   else {
                      layerLI = $('label[i18n="'+layer.title+'"]').parent();
                      MOSQUITO.app.mapView.loading.on(layerLI);
                      if (layer.key === 'F') MOSQUITO.app.mapView.refreshCoverageLayer();
                      else if (layer.key === 'Q') MOSQUITO.app.mapView.loadStormDrainData();
                      else if (layer.key === 'I') MOSQUITO.app.mapView.refreshForecastModel();
                      else if (layer.key === 'P') MOSQUITO.app.mapView.addEpidemiologyLayer();
                      else _this._map.addLayer(theLayer, function() {});
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
                if (typeof MOSQUITO.app.mapView !== 'undefined')
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
