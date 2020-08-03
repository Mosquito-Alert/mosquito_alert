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

        rebuildSelectPicker: function (select_year, select_month, newDatesAvailable){
            var key = $('#'+select_year).val()
            var options=''

            newDatesAvailable.forEach(function(y, i) {
              options += '<option value="'+y[0]+'"'
              if (i === 0)  options += ' selected';
              options +='>'+y[0]+'</option>'
            });

            $('#'+select_year).html(options)
            $('#'+select_year).selectpicker('refresh')
            $('#'+select_year).trigger('change')//refresh months for this year
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
                if (layer.layer._meta.key == 'M' && 'mapView' in MOSQUITO.app && 'forecatVectorFromat' in MOSQUITO.app.mapView &&
                     MOSQUITO.app.mapView.forecatVectorFromat=='grid') {

                  MOSQUITO.app.mapView.forecast_layer._meta = layer.layer._meta;
                  layer.layer = MOSQUITO.app.mapView.forecast_layer;
                }

                if (layer.layer._meta.key == 'M' && 'mapView' in MOSQUITO.app && 'forecatVectorFromat' in MOSQUITO.app.mapView &&
                     MOSQUITO.app.mapView.forecatVectorFromat=='municipalities') {
                  MOSQUITO.app.mapView.munis_vector_prob_layer._meta = layer.layer._meta;
                  layer.layer = MOSQUITO.app.mapView.munis_vector_prob_layer;
                }

                if (layer.layer._meta.key == 'N' && 'mapView' in MOSQUITO.app && 'munis_virus_prob_layer' in MOSQUITO.app.mapView) {
                  MOSQUITO.app.mapView.munis_virus_prob_layer._meta = layer.layer._meta;
                  layer.layer = MOSQUITO.app.mapView.munis_virus_prob_layer;
                }

                if (_this._map.hasLayer(layer.layer)) {
                    item.addClass('active');
                    item.closest('.collapse').prev().find('.layer-subgroup').addClass('active');

                    item.closest('#div_'+layer.group).prev().find('.layer-group').addClass('active');

                    _this.container.find('#id' + layer.group).attr('aria-expanded','true');
                    _this.container.find('#div_' + layer.group).attr('aria-expanded','true');
                    _this.container.find('#div_' + layer.group).attr('class','collapse in');
                    item.closest('.layer-group-trigger').addClass('active');
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
                //When group==models, if no models are available then skip the group "models"
                if (group.name == 'models' &&
                    !MOSQUITO.config.availableVectorData &&
                    !MOSQUITO.config.availableVirusData){
                      console.log('No models data available. Skipping group')
                      return false;
                }

                if (MOSQUITO.app.headerView.logged) var layersAll = MOSQUITO.config.logged.layers;
                else var layersAll = MOSQUITO.config.layers || this.options.layers;

                layers = []; //get all layers for each group
                subgroups =[] //get all subgroup of this group. Array to keep order
                layers_subgroup =[] //get all layers of this subgroup. Array to keep order
                layers_no_subgroup =[]
                ordering=[]
                for (var a=0;  a <layersAll.length; a++){
                    layer = layersAll[a];
                    if (layersAll[a].group == group.name){
                        layers.push(layer)
                        //only subgroups in this group
                        if ('subgroup' in layersAll[a]){
                          var thisSubgroup = layersAll[a].subgroup
                          var pos = subgroups.indexOf(thisSubgroup)
                          if (pos==-1){
                            subgroups.push(thisSubgroup)
                            ordering.push(a)
                            layers_subgroup.push([layersAll[a]])
                          }else{
                            layers_subgroup[pos].push(layersAll[a])
                          }
                        }
                        else{
                          //no subgroup present
                          ordering.push(a)
                          layers_no_subgroup.push(layersAll[a])
                        }
                    }
                }
                subgroups.push('none')
                layers_subgroup.push(layers_no_subgroup)
                //check user types

                var extra_class=' public'
                if (MOSQUITO.app.headerView.logged){
                    extra_class=' private'
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
                  var accordion = _this.doAccordion(list, group.name, 'layer-group list-group-item')
                  var divGroup = accordion.children

                }
                else{ //if group == none
                  var divGroup = $('<div>')
                      .attr('id', 'div_'+group.name)
                      .attr('class', extra_class)
                  .appendTo(list);
                }

                // var ulGroup = $('<ul>').attr('id', 'ul_'+group.name).appendTo(divGroup);

                //Iterate all layers of one subgroup
                $.each(subgroups, function(i, subgroup){
                  if (subgroups[i]!='none'){
                    //no geohashBounds

                    var subAccordion = _this.doAccordion(divGroup, subgroup,'layer-subgroup list-group-item'+extra_class)
                    var divSubgroup = subAccordion.children
                    divSubgroup.appendTo(divGroup)
                  }else{
                    var divSubgroup = $('<div>')
                        .attr('id', 'div_'+group.name)
                    .appendTo(divGroup);
                  }

                  var ulSubgroup = $('<ul>')
                    .attr('id', 'ul_'+subgroup)
                    .attr('class', extra_class)
                    .appendTo(divSubgroup);

                  //Iterate all layers of one group
                  layers = layers_subgroup[i]

                  $.each(layers, function(i, layer) {
                    //Some layers have conditions to be shown
                    if (layer.key=='Q' && (!isManager && !isSuperUser)){
                      return true
                    }

                    classname = (group.name != 'none')?'list-group-item':'list-group-only-item';
                    //clicable item add/removes layer from map
            		    var item = $('<li>')
                        .attr('class', classname)
                        .attr('id', 'layer_'+layer.key)
                        .appendTo(ulSubgroup);

                    switch (layer.key) {
                        case 'E':  //Different types of breeding sites
                            $('<label i18n="'+layer.title+'" class="multiclass">').appendTo(item);
                            var sublist = $('<ul>').attr('class', 'sub-sites').appendTo(item);
                            for (var cat in layer.categories) {
                              var subitem = $('<li>').attr('class', 'sublist-group-item').appendTo(sublist);
                              $('<img>').attr('src', 'img/marker_'+cat+'.svg').attr('class', 'icon').appendTo(subitem);
                              $('<label i18n="map.'+cat+'">').appendTo(subitem);
                            }
                            break;
                        case 'R':
                          options={
                            'infoIconId': 'bitingInfoIcon',
                            'infoPopup': 'layer.biting.description',
                            'infoIcon': 'fa fa-question question-mark-toc',
                            'forecastMonthId': 'monthBitingLayer',
                            'forecastYearId': 'yearBitingLayer',
                            'legendTitle':'bitting.legend-title',
                            'forecastSd': 'forecast_sd',
                            'visibleFromZoom': 7
                          }
                          _this.addBitingsUI(layer,item, options)
                          break;
                        case 'F': // user fixes
                            _this.addLayerFixesUI(layer,item);
                            break;
                        case 'M': // Forecast models
                            options={
                              'infoPopup': 'layer.predictionmodels.description',
                              'infoIcon': 'fa fa-question question-mark-toc',
                              'infoIconId': 'municipalityGrid',
                              'forecastMonthId': 'monthVectorMunicipalityProb',
                              'forecastYearId': 'yearVectorMunicipalityProb',
                              'legendTitle':'models.probability',
                              'forecastSd': 'forecast_sd',
                              'visibleFromZoom': 7,
                              'availableModelsDates': 'municipalities_models_available',
                              'selectRegionId': 'selectRegionVectorModel',
                              'selectId': 'selectVectorId',
                              'kindSelectorText': 'layer.models.vector'
                            }
                            mode = 'vector'
                            //if logged default is municipalities models
                            if (MOSQUITO.app.headerView.logged){
                              modelDates=MOSQUITO.config.vector_municipalities
                            }else{
                              modelDates=MOSQUITO.config.vector_grid
                            }

                            if (MOSQUITO.config.availableVectorData){
                              _this.modelsUI(layer, item, options, mode, modelDates)
                            }
                            break;
                        case 'N': // Forecast models
                            options={
                              'infoPopup': 'layer.predictionmodels.viruscontent',
                              'infoIcon': 'fa fa-question question-mark-toc',
                              'infoIconId': 'virusToolTip',
                              'forecastMonthId': 'monthVirusMunicipalityProb',
                              'forecastYearId': 'yearVirusMunicipalityProb',
                              'legendTitle':'models.probability',
                              'forecastSd': 'forecast_sd',
                              'visibleFromZoom': 7,
                              'availableModelsDates': 'virus_models_available',
                              'selectRegionId': 'selectRegionVirusModel',
                              'selectId': 'selectVirusId',
                              'kindSelectorText': 'layer.models.virus'
                            }
                            mode = 'virus'
                            modelDates=MOSQUITO.config.virus_municipalities

                            if (MOSQUITO.config.availableVirusData){
                              _this.modelsUI(layer, item, options, mode, modelDates)
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

                        default: //observation layers
                            $('<img>').attr('src', layer.icon).attr('class', 'icon').appendTo(item);
                            $('<label i18n="'+layer.title+'">').appendTo(item);
                        break;
                    }

                    //when click on a layer selector
                		item.on('click', function(event) {
                      // layerLI = $('label[i18n="'+layer.title+'"]').parent();
                      layerLI = $('li#layer_'+layer.key)
                         if (layer.key === 'M') {
                          //When logged, models layers loads on municipality format
                          MOSQUITO.app.mapView.forecatVectorFromat='municipalities'
                          metaLayer=MOSQUITO.app.mapView.munis_vector_prob_layer
                          theLayer = MOSQUITO.app.mapView.munis_vector_prob_layer;

                          MOSQUITO.app.mapView.munis_vector_prob_layer._meta = {
                            'key': 'M',
                            'icon': "img/epi_confirmed.svg",
                            'layer': metaLayer
                          };

                          if (MOSQUITO.app.headerView.logged){
                            //if user is logged check for grid format on this layer
                            if ($("input[name='modelType']:checked").val()=='grid'){
                              MOSQUITO.app.mapView.forecatVectorFromat='grid'
                              metaLayer=MOSQUITO.app.mapView.forecast_layer
                              theLayer = MOSQUITO.app.mapView.forecast_layer;
                              MOSQUITO.app.mapView.forecast_layer._meta = {
                                'key': 'M',
                                'icon': "img/epi_confirmed.svg",
                                'layer': metaLayer
                              };
                            }
                          }
                          else{
                            //if not logged show only grid layer
                            MOSQUITO.app.mapView.forecatVectorFromat='grid'
                            metaLayer=MOSQUITO.app.mapView.forecast_layer
                            theLayer = MOSQUITO.app.mapView.forecast_layer;
                            MOSQUITO.app.mapView.forecast_layer._meta = {
                              'key': 'M',
                              'icon': "img/epi_confirmed.svg",
                              'layer': metaLayer
                            };
                          }

                          // When we unfold the select
                          var option = event.target;
                          if ($(option).hasClass('filter-option') ||
                                $(option).hasClass('caret') ||
                                $(option).hasClass('dropdown-toggle')) {
                                  return;
                                }
                          // when we pick an option
                          // ... because we clicked on the span.text

                          if (option.tagName === 'A') option = event.target.children[0];
                        }
                        else if (layer.key === 'N') {
                            metaLayer= MOSQUITO.app.mapView.munis_virus_prob_layer
                            theLayer = MOSQUITO.app.mapView.munis_virus_prob_layer;

                            MOSQUITO.app.mapView.munis_virus_prob_layer._meta = {
                              'key': 'N',
                              'icon': "img/epi_confirmed.svg",
                              'layer': metaLayer
                            };

                            // When we unfold the select
                            var option = event.target;
                            if ($(option).hasClass('filter-option') ||
                                  $(option).hasClass('caret') ||
                                  $(option).hasClass('dropdown-toggle')) {
                                    return;
                                  }
                            // when we pick an option
                            // ... because we clicked on the span.text

                            if (option.tagName === 'A') option = event.target.children[0];
                          }
                        else if (layer.key === 'R') {

                            metaLayer= MOSQUITO.app.mapView.biting_layer
                            theLayer = MOSQUITO.app.mapView.biting_layer;

                            MOSQUITO.app.mapView.biting_layer._meta = {
                              'key': 'R',
                              'layer': metaLayer
                            };

                            // When we unfold the select
                            var option = event.target;
                            if ($(option).hasClass('filter-option') ||
                                  $(option).hasClass('caret') ||
                                  $(option).hasClass('dropdown-toggle')) {
                                    return;
                                  }
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
                          loadLayer = false
                          if (layer.key === 'M') {
                            //reload layer when click on radio or select
                            if ('type' in $(option)[0] && $(option)[0].type=='radio') {
                                //when event occurs then reload
                                MOSQUITO.app.mapView.refreshVectorProbMunisModel();
                                loadLayer=true
                            }
                            else {
                              if ( $(option).hasClass('text')) {
                                if ($('#selectRegionVectorModel').val()!=''){
                                  MOSQUITO.app.mapView.refreshVectorProbMunisModel();
                                  loadLayer=true
                                }else{
                                  _this._map.removeLayer(theLayer);
                                }
                              }
                              else{
                                _this._map.removeLayer(theLayer);
                              }
                            }
                          }
                          else if (layer.key === 'N') {
                                  if ( $(option).hasClass('text')) {
                                    if ($('#selectRegionVirusModel').val()!=''){
                                      loadLayer=true
                                      MOSQUITO.app.mapView.refreshVirusProbMunisModel();
                                    }else{
                                      _this._map.removeLayer(theLayer);
                                    }

                                  }
                                  else{
                                    _this._map.removeLayer(theLayer);
                                  }
                                }
                          else if (layer.key === 'R') {
                                  if ( $(option).hasClass('text')) {
                                    MOSQUITO.app.mapView.refreshBitingLayer();
                                  }
                                  else{
                                    _this._map.removeLayer(theLayer);
                                  }
                                }
                          else {

                            _this._map.removeLayer(theLayer);
                            //update map counter
                            _this._map.fire('layerchange', {
                                layer : theLayer
                            });
                            if (layer.key=='Q') {
                              _this._map.off('click', MOSQUITO.app.mapView.checkStormDrainInfo);
                            }
                          }
                      }
                      else {
                          loadLayer = true
                          if (layer.key === 'F') MOSQUITO.app.mapView.refreshCoverageLayer();
                          else if (layer.key === 'Q'){
                            MOSQUITO.app.mapView.loadStormDrainData();
                            //if stormdrain data has been already loaded, then
                            //no loading gif must appear because it will never disappear
                            if (MOSQUITO.app.mapView.stormDrainData.length!=0){
                              loadLayer = false;
                            }
                          }
                          // else if (layer.key === 'I') MOSQUITO.app.mapView.refreshForecastModel();
                          else if (layer.key === 'M') {
                            var modelType = $("input[name='modelType']:checked").val();
                            if (modelType=='grid'){
                              MOSQUITO.app.mapView.refreshForecastModel();
                            }else{
                              if ($('#selectRegionVectorModel').val()!=''){
                                MOSQUITO.app.mapView.refreshVectorProbMunisModel();
                              }else{
                                loadLayer = false
                              }
                            }
                          }
                          else if (layer.key === 'N') {
                              if ($('#selectRegionVirusModel').val()!=''){
                                MOSQUITO.app.mapView.refreshVirusProbMunisModel()
                              }else{
                                loadLayer = false
                              }
                          }
                          else if (layer.key === 'R') {
                                MOSQUITO.app.mapView.refreshBitingLayer()
                          }
                          else if (layer.key === 'P') MOSQUITO.app.mapView.addEpidemiologyLayer();
                          else { //Just adding a simple observations layer. Show loading here
                            loadLayer=false
                            MOSQUITO.app.mapView.loading.on(layerLI);
                            _this._map.addLayer(theLayer, function() {});
                            //update map counter
                            _this._map.fire('layerchange', {
                                layer : theLayer
                            });
                          }
                      }

                      if (loadLayer){
                        //load models data.
                        MOSQUITO.app.mapView.loading.on(layerLI);
                      }

                      // activate/deactivate subgroups if apply
                      if (subgroup != 'none'){
                        if ($('#div_'+subgroup).find('li.active').length == 0) {
                          divSubgroup.closest('.collapse').prev().find('.layer-subgroup').removeClass('active');
                        }
                        else{
                          divSubgroup.closest('.collapse').prev().find('.layer-subgroup').addClass('active');
                        }
                      }
                      //activate/deactivate groups if apply
                      if (group.name != 'none'){
                        if ($('#div_'+group.name).find('li.active').length == 0) {
                          divGroup.closest('.collapse').prev().find('.layer-group').removeClass('active');
                        }
                        else{
                          divGroup.closest('.collapse').prev().find('.layer-group').addClass('active');
                        }
                      }
                		});
                  });//end each layer
                }); //end each subgroup
            }); //end each group

            this.setActiveClass();

    		    this._map.on('layeradd', function(layer) {

              if('_meta' in layer.layer){
                var item = section.find('#layer_'+ layer.layer._meta.key) ;

                item.addClass('active');
                item.parent().parent().prev().find('.layer-group').addClass('active');
                if (typeof MOSQUITO.app.mapView !== 'undefined'){
                  MOSQUITO.app.mapView.loading.off(item);
                }
              }
      			});

            this._map.on('layerremove', function(layer) {
              if('_meta' in layer.layer){
                var item = section.find('#layer_'+ layer.layer._meta.key);
                item.removeClass('active');
              }
    			  });

          return this.container;

        }
        ,
        doAccordion:function(list, group_name, class_name){
          var father = $('<div/>')
              .attr('data-toggle','collapse')
              .attr('data-target', '#div_'+group_name)
              .attr('class','layer-group-trigger')
              .attr('aria-expanded',"false")
              .attr('id', 'id' + group_name)
          .appendTo(list);

          var parentDiv = $('<div/>')
              .attr('class', class_name)
          .appendTo(father);

          $('<div/>')
             .attr('i18n', 'group.'+group_name)
             .attr('class','group-title')
         .appendTo(parentDiv)

//////////////////////////
        //Question mark (popover text) only for certain accordion groups
        var excludedGroups=['tiger', 'zika','koreicus', 'japonicus', 'culex']
        if (excludedGroups.indexOf(group_name)===-1 ){
            let question_mark = $('<a>', {
              'tabindex':'0',
              'role': 'button',
              'data-trigger': 'focus',
              // 'data-toggle':'popover-filters',
              'data-placement':'left',
              'i18n': group_name + '.description|data-content',
              'data-container': 'body',
              'class':'fa fa-question question-mark-toc question-mark-filters',
              'id': 'question_mark_filters',
            })
            var questionDiv = $('<div>')
              .attr('id', 'question_mark_container')

            question_mark.appendTo(questionDiv)
            questionDiv.appendTo(parentDiv)

            // $(document).click(function(e) {
            //   var isVisible = $("[data-toggle='popover-filters']").data('bs.popover').tip().hasClass('in');
            //   if (isVisible){
            //     question_mark.click()
            //     return false;
            //   }
            // });

            question_mark.on('click', function(event) {
             event.stopPropagation();
             return false;
            });

            $(question_mark).popover({
              html: true,
              // trigger: 'focus',
              content: function() {
                return true;
                }
            })
        };
//////////////////////////
          var icon = $('<div/>')
              .attr('class', 'layer-group-icon')
              .attr('aria-hidden','true')

          var children = $('<div>')
              .attr('id', 'div_'+group_name)
              .attr('class', 'collapse')
          .appendTo(list);

          return {'father': father, 'children': children}
        },

        addBitingsUI: function (layer, item, options){
          var _this = this

          var labelContainer = $('<div>')
            .attr('id', 'layer-title-container')
            .appendTo(item)

          $('<label i18n="'+layer.title+'" class="multiclass">').appendTo(labelContainer);

          // QUESTION MARK
          let question_mark = $('<a>', {
            'tabindex':'0',
            'role': 'button',
            'data-trigger': 'focus',
            'id': options.infoIconId,
            'data-toggle':'popover',
            'data-placement':'left',
            'i18n': options.infoPopup+'|data-content',
            'data-container': 'body',
            'class':options.infoIcon
          })

          question_mark.appendTo(labelContainer)
          question_mark.on('click', function(event) {
            event.stopPropagation();
            return false;
          });

          $(question_mark).popover({
            html: true,
            content: function() {
              return true;
              }
          });

          // LISTEN ANY CLICK TO HIDE POPOVER
          // $(document).click(function(e) {
          //   var isVisible = $("#"+options.infoIconId).data('bs.popover').tip().hasClass('in');
          //   if (isVisible){
          //     question_mark.click()
          //   }
          //   if (_this.highlight_layer){
          //     _this.map.removeLayer(_this.highlight_layer)
          //   }
          // });

          //when user is not logged, print species selector for vector municipalities model
          var date_selector = $('<div>', {'id': 'forecast_date_selector'})
            .appendTo(item);

          // DATE SELECTOR
          var months = MOSQUITO.config.months;
          var first_time_loading = true;
          var this_month = new Date().getMonth();//current month

          //YEAR
          $('<div>', {'style': 'clear:both'}).appendTo(item);
          var date_selector = $('<div>', {'id': 'forecast_date_selector'})
            .appendTo(item);

          $('<div>', {'i18n': 'general.year'}).css('padding', '5px')
            .css('width', 45)
            .appendTo(date_selector);

          var year_select = $('<select>', {
              'name': options.forecastYearId,
              'id': options.forecastYearId,
              'class': 'selectpicker dropup'}
            ).appendTo(date_selector)
            .on('change', function(e) {
              let year = $(this).val();
              let index = $(this).prop('selectedIndex')
              let months_availability = [];

              months_availability = MOSQUITO.config['availableBitingData'][index][1];

              previous_month = $(month_select).val() - 1
              month_select.empty();
              months.forEach(function(month, i) {
                let attrs = {'value': i + 1, 'i18n': month};
                if (months_availability[i] === 0) attrs['disabled'] = 'false';
                month_select.append($('<option>', attrs));
              });
              t().translate(MOSQUITO.lng,month_select);

              let option=''
              //current month selected by default
              if (first_time_loading) {
                option = $('#' + options.forecastMonthId + ' option')[this_month];
              }
              else{
                option = $('#' + options.forecastMonthId + ' option')[previous_month];
              }
              // if current month is disabled, check closest previous available month
              if ($(option).is(':disabled')){
                $(option).parent().find('option').not(':disabled')[0]
              }else{
                $(option).attr('selected', 'selected');
              }

              month_select.selectpicker('refresh');
              first_time_loading = false;
            });  //end year onchange

            $('<div>', {'style': 'clear:both'}).appendTo(item);
            // MONTH
            var date_selector = $('<div>', {'id': 'forecast_date_selector'})
              .appendTo(item);
            $('<div>', {'i18n': 'general.month'}).css('padding', '5px')
                .css('width', 45)
                .appendTo(date_selector);
            var month_select = $('<select>', {
                'name': options.forecastMonthId,
                'id': options.forecastMonthId,
                'class': 'selectpicker dropup'}
              ).appendTo(date_selector);
            var availableMonths = MOSQUITO.config['availableBitingData']
            availableMonths.forEach(function(y, i) {
              let attrs = {'value': y[0]};
              if (i === 0) attrs['selected'] = 'selected';
              year_select.append($('<option>', attrs).html(y[0]));
            });

            setTimeout(function() {year_select.change()}, 100);
            $('<div>', {'style': 'clear:both'}).appendTo(item);
            options.sd_legend = MOSQUITO.config.show_bitting_sd
            this.setLegend(layer, item, options)
        },

        addLayerFixesUI: function(layer,item){

          //question mark (popover info text)
          var labelContainer = $('<div>')
            .attr('id', 'layer_F')
            .appendTo(item)

          $('<label i18n="'+layer.title+'" class="multiclass">').appendTo(labelContainer);

          // QUESTION MARK
          let question_mark = $('<a>', {
            'tabindex':'0',
            'role': 'button',
            'data-trigger': 'focus',
            'id': options.infoIconId,
            'data-toggle':'popover',
            'data-placement':'left',
            'i18n': 'layer.userfixes.description|data-content',
            'data-container': 'body',
            'class':options.infoIcon
          })

          question_mark.appendTo(labelContainer)
          question_mark.on('click', function(event) {
            event.stopPropagation();
            return false;
          });

          $(question_mark).popover({
            html: true,
            content: function() {
              return true;
              }
          });

          var sublist = $('<ul>').attr('class', 'sub-sites').appendTo(item);
          // get the segments for the legend
          for (i=0;i<layer.segments.length;++i) {
              var subitem = $('<li>').attr('class', 'sublist-group-item').appendTo(sublist);
              // category image
              var color = (layer.segmentationkey == 'color') ? layer.segments[i].color : layer.style.fillColor;
              var opacity = (layer.segmentationkey == 'opacity') ? layer.segments[i].opacity : layer.style.fillOpacity;
              var strokecolor = ((layer.color_border!='')?layer.color_border:'black')
              $('<div>')
                .css('width', 20)
                .css('height', 20)
                .css('background','rgb('+color+')')
                .css('border', '1px solid '+strokecolor)
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
        },

        modelsUI: function (layer, item, options, mode, modelAvailableDates){
          var _this = this

          var labelContainer = $('<div>')
            .attr('id', 'layer-title-container')
            .appendTo(item)

          $('<label i18n="'+layer.title+'" class="multiclass">').appendTo(labelContainer);

          // QUESTION MARK
          let question_mark = $('<a>', {
            'tabindex':'0',
            'role': 'button',
            'data-trigger': 'focus',
            'id': options.infoIconId,
            'data-toggle':'popover',
            'data-placement':'left',
            'i18n': options.infoPopup+'|data-content',
            'data-container': 'body',
            'class':options.infoIcon
          })

          question_mark.appendTo(labelContainer)
          question_mark.on('click', function(event) {
            event.stopPropagation();
            return false;
          });

          $(question_mark).popover({
            html: true,
            content: function() {
              return true;
              }
          });

          // LISTEN ANY CLICK TO HIDE POPOVER
          $(document).click(function(e) {
            var isVisible = $("#"+options.infoIconId).data('bs.popover').tip().hasClass('in');
            if (isVisible){
              question_mark.click()
            }
            if (_this.highlight_layer){
              _this.map.removeLayer(_this.highlight_layer)
            }
          });

          //REGION SELECTOR
          var ccaa = MOSQUITO.config.ccaa;
          //RADIO TYPE SELECTION
          if (MOSQUITO.app.headerView.logged){
              if (mode=='vector'){
                var model_selector = $('<div>', {'id': 'forecast_date_selector', 'class':'model-type'})
                  .appendTo(item);
                $('<span i18n="models.type" class="models-type-label">').appendTo(model_selector);

                var container = $('<div class="types1">').appendTo(model_selector)
                var subcontainer = $('<div class="types2">').appendTo(container)

                $('<input type="radio" id="modelType" name="modelType" value="grid" />').appendTo(subcontainer);
                $('<span i18n="models.type.grid">').appendTo(subcontainer);

                var subcontainer = $('<div class="types3">').appendTo(container)
                $('<input type="radio" id="modelType" name="modelType" value="municipalities" checked="true"/>').appendTo(subcontainer);
                $('<span i18n="models.type.municipalities">').appendTo(subcontainer);

                let previousRadioValue=''
                $(container).on('mousedown', function(e){
                    if ('type' in e.target){
                      previousRadioValue = $("input[name='modelType']:checked").val()
                    }
                })

                $(container).on('click', function(e){
                    if ('type' in e.target){
                      newValue = $("input[name='modelType']:checked").val()
                      if (newValue=='grid'){
                        availableDates = MOSQUITO.config.vector_grid
                        $('.ccaa-selector').hide()
                      }else{
                        availableDates = MOSQUITO.config.vector_municipalities
                        $('.ccaa-selector').show()
                      }
                      $("input[name=modelType]:checked").attr('checked', true);

                      var types = MOSQUITO.config.available_vectors_selector
                      var vector_select = $('#' + options.selectId);
                      var vectorValue = $('#'+options.selectId).val()

                      if (availableDates[vectorValue]===null){
                        var newAvailableValue=''
                        $('#' + options.selectId +' option').each(function(){
                          var disabled='false'
                          if (availableDates[this.value]===undefined){
                              $(this).attr('disabled','true');
                          }else{
                            $(this).removeAttr('disabled');
                            newAvailableValue = this.value
                            $('#' + options.selectId).val(newAvailableValue)
                          }
                        });
                        vectorValue = newAvailableValue
                      }

                      vector_select.selectpicker('refresh')
                      if (newAvailableValue!=''){
                        _this.rebuildSelectPicker(options.forecastYearId, options.forecastMonthId, availableDates[vectorValue])
                      }else{
                        //if no mosquito dates available then remove layer from map
                        e.stopPropagation();
                        _this._map.removeLayer(MOSQUITO.app.mapView.forecast_layer)
                        _this._map.removeLayer(MOSQUITO.app.mapView.munis_vector_prob_layer)
                      }
                    } // end type in e.target

                    currentValue = $("input[name='modelType']:checked").val()
                    var getRegionFirst = false
                    if (currentValue=='municipalities' && previousRadioValue=='grid'){
                      getRegionFirst = true
                    }
                    //With no timeout, event could be fired before listener is added
                    //needs review
                    setTimeout(function(){
                        $(document).trigger('models_radio_clicked', getRegionFirst)
                      },0);
                    // e.stopPropagation();
                    // e.preventDefault();
                })
              }// fi mode vector and logged user

              var date_selector = $('<div>', {
                  'id': 'forecast_date_selector',
                  'class': 'cara'
                })
                .appendTo(item);

              $('<div>', {'i18n': options.kindSelectorText}).css('padding', '5px')
                .css('width', 45)
                .appendTo(date_selector);
              var v_select = $('<select>', {
                  'name': options.selectId,
                  'id': options.selectId,
                  'class': 'selectpicker dropup'})
                .appendTo(date_selector)

              var availableDates=[]
              availableDates = modelAvailableDates

              if (mode=='virus'){
                var types = MOSQUITO.config.available_virus_selector
              }
              else{
                var types = MOSQUITO.config.available_vectors_selector
              }

              types.forEach(function(ele) {
                let attrs = {'value': ele.k, 'i18n': ele.v};
                if (availableDates[ele.k]===undefined){
                  attrs.disabled='true';
                }
                v_select.append($('<option>', attrs).html(ele.v));
              });

              $(v_select).on("changed.bs.select",
                    function(e, clickedIndex, newValue, oldValue) {
                  _this.rebuildSelectPicker(options.forecastYearId, options.forecastMonthId, availableDates[this.value])
              })
          } //end if logged
          else{
            //when user is not logged, print species selector for vector municipalities model
            var date_selector = $('<div>', {'id': 'forecast_date_selector'})
              .appendTo(item);

            $('<div>', {'i18n': options.kindSelectorText}).css('padding', '5px')
              .css('width', 45)
              .appendTo(date_selector);

            var vector_select = $('<select>', {
                'name': options.selectId,
                'id': options.selectId,
                'class': 'selectpicker dropup'})
              .appendTo(date_selector)

            var types = MOSQUITO.config.available_vectors_selector
            types.forEach(function(ele) {
              let attrs = {'value': ele.k, 'i18n': ele.v};
              if (MOSQUITO.config.vector_municipalities[ele.k]===undefined){
                attrs.disabled='true';
              }
              vector_select.append($('<option>', attrs).html(ele.v));
            });

            $(vector_select).on("changed.bs.select",
                  function(e, clickedIndex, newValue, oldValue) {
                newDatesAvailable = modelDates[this.value]
                _this.rebuildSelectPicker(options.forecastYearId, options.forecastMonthId, newDatesAvailable)

            })
          }
          // DATE SELECTOR
          var months = MOSQUITO.config.months;
          // SELECTORS
          var date_selector = $('<div>', {'id': 'forecast_date_selector', 'class': 'ccaa-selector'})
            .appendTo(item);

          //Region label
          if (MOSQUITO.app.headerView.logged){
              $('<div>', {'i18n': 'general.select-region'}).css('padding', '5px')
                .css('width', 45)
                .appendTo(date_selector);

              var ccaa_select = $('<select>', {
                  'name': options.selectRegionId,
                  'id': options.selectRegionId,
                  'class': 'selectpicker dropup'})
                .on('change', function(e) {
                  var pre = $(this).data('pre')
                  $(this).data('prev', pre)
                  $(this).data('pre', $(this).val())
                })
                .appendTo(date_selector)

              ccaa.forEach(function(ele) {
                let attrs = {'value': ele.k, 'i18n': ele.v};
                ccaa_select.append($('<option>', attrs).html(ele.v));
              });
          } //End Spanish regions selector

          var first_time_loading = true;
          var this_month = new Date().getMonth();

          //YEAR
          $('<div>', {'style': 'clear:both'}).appendTo(item);
          var date_selector = $('<div>', {'id': 'forecast_date_selector'})
            .appendTo(item);

          $('<div>', {'i18n': 'general.year'}).css('padding', '5px')
            .css('width', 45)
            .appendTo(date_selector);

          var year_select = $('<select>', {
              'name': options.forecastYearId,
              'id': options.forecastYearId,
              'class': 'selectpicker dropup'}
            ).appendTo(date_selector)
            .on('change', function(e) {
              let year = $(this).val();
              let found = false;
              let i = 0;
              let months_availability = [];

              var specie = $('#'+options.selectId).val()
              //only months with models available
              if (mode == 'vector'){
                if (MOSQUITO.app.headerView.logged){
                  if ($("input[name='modelType']:checked").val()=='grid'){
                    var model = 'vector_grid'
                  }else{
                    var model = 'vector_municipalities'
                  }
                }
                else{
                  var model = 'vector_grid'
                }
              }else{
                 var model = 'virus_municipalities'
               }

             if (specie in MOSQUITO.config[model]){
               while (i < MOSQUITO.config[model][specie].length && !found) {
                 if (MOSQUITO.config[model][specie][i][0] == year) {
                   found = true;
                   months_availability = MOSQUITO.config[model][specie][i][1];
                 } else ++i;
               }
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
              //current month selected by default
              if (first_time_loading) {
                option = $('#' + options.forecastMonthId + ' option')[this_month];
              }
              else{
                option = $('#' + options.forecastMonthId + ' option')[previous_month];
              }
              // if current month is disabled, check closest previous available month
              if ($(option).is(':disabled')){
                $(option).parent().find('option').not(':disabled')[0]
              }else{
                $(option).attr('selected', 'selected');
              }

              month_select.selectpicker('refresh');
              first_time_loading = false;
            });  //end onchange

            $('<div>', {'style': 'clear:both'}).appendTo(item);
            // MONTH
            var date_selector = $('<div>', {'id': 'forecast_date_selector'})
              .appendTo(item);
            $('<div>', {'i18n': 'general.month'}).css('padding', '5px')
                .css('width', 45)
                .appendTo(date_selector);
            var month_select = $('<select>', {
                'name': options.forecastMonthId,
                'id': options.forecastMonthId,
                'class': 'selectpicker dropup'}
              ).appendTo(date_selector);

            firstKey = Object.keys(modelAvailableDates)[0]
            modelAvailableDates[firstKey].forEach(function(y, i) {
              let attrs = {'value': y[0]};
              if (i === 0) attrs['selected'] = 'selected';
              year_select.append($('<option>', attrs).html(y[0]));
            });

            setTimeout(function() {year_select.change()}, 100);
            $('<div>', {'style': 'clear:both'}).appendTo(item);

            this.setLegend(layer, item, options)
        }
        ,

        setLegend: function (layer, item, options){
          var sublist = $('<ul>').attr('class', 'sub-sites').css('font-weight', 'bold').css('float', 'left').appendTo(item);
          sublist.append($('<h5>', {'i18n': options.legendTitle}));
          ind=0
          layer.prob_ranges.forEach(function(range) {
            hover_label = 'models.hover-prob-label'+ind
            var subitem = $('<li>')
              .attr('i18n', hover_label+'|title')
              .attr('class', 'sublist-group-item').appendTo(sublist);

            $('<div>')
              .css('width', 20)
              .css('height', 20)
              .css('background',range.color)
              .css('border', '1px solid '+((layer.color_border_prob!='')?layer.color_border_prob:'orange'))
              .css('float', 'left')
              .css('margin-right', '10px')

              .appendTo(subitem);
            $('<label>', {'i18n': range.label}).appendTo(subitem);
            ind = ind + 1
          });

          //break if no sd legend is required
          if ( ('sd_legend' in options) && (options.sd_legend==false) ){
            return true;
          }
          else{
            // LEGEND ST. DEV.
            sublist = $('<ul>', {'class': 'sub-sites '+options.forecastSd,})
              .css('font-weight', 'bold')
              .css('float', 'left')
              .appendTo(item);

            sublist.append($('<h5>', {'i18n': 'models.uncertainty'}));
            ind=0

            layer.sd_ranges.forEach(function(range) {
              hover_label = 'models.hover-sd-label'+ind
              var subitem = $('<li>')
                .attr('i18n', hover_label+'|title')
                .attr('class', 'sublist-group-item').appendTo(sublist);

            $('<div>')
              .css('width', 14)
              .css('height', 14)
              .css('background',range.color)
              .css('border', '1px solid '+((layer.color_border_sd!='')?layer.color_border_sd:'black'))
              .css('border-radius', '50%')
              .css('float', 'left')
              .css('margin-right', '10px')
              .css('margin', '3px 10px 0 0px')
              .appendTo(subitem);
            $('<label>', {'i18n': range.label}).appendTo(subitem);
              ind = ind + 1
            });
            if (map.getZoom() <= options.visibleFromZoom) {
              sublist.css('opacity', '.3');
            } else {
              sublist.css('opacity', '1');
            }
          } //end else sd legend
        }
        ,

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
