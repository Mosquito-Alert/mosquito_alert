var MapView = MapView.extend({

    addZoomControl: function(){
        this.controls.zoom = new L.Control.Zoom(
            {position: 'topright'}).addTo(this.map);
    },

    sideBar: function(){
        if(typeof(this.controls.sidebar) === 'undefined'){
            this.controls.sidebar = L.OSM.sidebar('#map-ui')
                .addTo(this.map);
            this.map.on('click', function(e){
                if (this.scope.selectedMarker){
                    this.controls.sidebar.closePane();
                }
            }, this);
        }

        return this.controls.sidebar;
    },

    addPanelLayersControl: function(){
        var layers = $.extend({}, this.LAYERS_CONF);
        var key;
        for(var i in layers){
            key = layers[i].key;
            layers[i].layer = this.layers.layers[key];
            layers[i].icon = this.getIconUrlByIndex(i);
        }
        var btn = new MOSQUITO.control.ControlLayers(
            {
                position: 'topright',
                sidebar: this.sideBar(),
                active: !this.isMobile(),
                layers: layers,
                text: '<i class="fa fa-bars" aria-hidden="true"></i>'/*,
                title: t('map.control_layers')*/
            }
        );
        this.controls.layers_btn = btn.addTo(this.map);
        $(btn._container).find('a').attr('i18n', 'map.control_layers|title');
        MOSQUITO.layers_btn = btn;
    },

    addNumReportsControl: function(){

        var content = '<span i18n="map.showed_reports"></span> ';
        content += '<span class>{0}</span>';
        var pnl = new MOSQUITO.control.CustomDIV(
            {
                position: 'bottomleft',
                content: content.replace('{0}', 0),
                style:'total_elements'
            }
        );
        this.controls.reports = pnl.addTo(this.map);
        this.map.on('movestart', function(){
            $(pnl.el).find('span').eq(1).html('0');
        });
        MOSQUITO.app.on('cluster_drawn', function(e){
        //this.map.on('cluster_drawn', function(e){
            $(pnl.el).find('span').eq(1).html(e.n);
        });

    },

    addFiltersInPanelLayers: function(){
        var _this = this;
        _.extend(this.filters, Backbone.Events);

        var container = $('div.sidebar-control-layers');

        //Filters
        var years = [ ['all', t('All years')] ];
        var current_year = new Date().getFullYear();
        for(var i = 2014; i <= current_year; i++){
            years.push([i,i]);
        }

        var filtersSection = $('<div>')
            .attr('id', 'map_filters')
            .attr('class', 'section filters')
            .appendTo(container);

        var select_years = $('<select>')
            .attr('class', 'years')
            .appendTo(filtersSection);

        $.each(years, function(i, year) {
            var opt = $('<option>', {value: year[0]})
                  .text(year[1]).appendTo(select_years);
            if(i === 0){
                opt.attr('i18n', year[1]);
            }
            if(_this.filters.year === parseInt(year[0])){
                opt.attr('selected', 'selected');
            }
        });

        select_years.on('change', function(){
            var year = $(this).val();
            if(year === 'all'){
              year = null;
            }else{
              year = parseInt(year);
            }
            _this.filters.trigger('year_change', year);
        });

        var months = [
          ['all', t('All months')],
          ['1', t('January')], ['2', t('February')], ['3', t('March')],
          ['4', t('April')], ['5', t('May')], ['6', t('June')],
          ['7', t('July')], ['8',t('August')], ['9', t('September')],
          ['10', t('October')], ['11', t('November')],
          ['12', t('December')]
        ];

        var select_months = $('<select multiple>')
              .attr('class', 'months')
              .appendTo(filtersSection);
        $.each(months, function(i, month) {
            var opt = $('<option>',
              {
                  value: month[0],
                  i18n: month[1]
              })
              .text(month[1]);

            if(_this.filters.months.length > 0 &&
                _this.filters.months.indexOf(parseInt(month[0])) !== -1){
                opt.attr('selected', 'selected');
            }

            select_months.append(opt);
        });

        if(_this.filters.months.length === 0){
            select_months.val('all');
        }

        select_months.data('pre', select_months.val());

        select_months.on('change', function(){
            var pre = $(this).data('pre');
            var now = $(this).val();
            if(pre.indexOf('all') !== -1 && pre.indexOf('all') !== -1){
                var newdata = $(this).val();
                if(newdata!==null){
                    newdata.shift();
                    $(this).val(newdata);
                }else{
                    $(this).val('all');
                }
            }else if((now === null) || (pre.indexOf('all') === -1 && now.indexOf('all') !== -1)){
                $(this).val('all');
            }
            $(this).selectpicker('refresh');
            var months = $(this).val();
            $(this).data('pre', $(this).val());
            if(months[0] === 'all'){
                months = [];
            }else{
                months =_.map(months, Number);
            }
            _this.filters.trigger('months_change', months);

        });

        trans.on('i18n_lang_changed', function(){
          setTimeout(function(){
              select_years.selectpicker('refresh');
              select_months.selectpicker('refresh');
          }, 0);
        });


    },

    addPanelMoreinfoControl: function(){
        var btn = new MOSQUITO.control.ControlMoreinfo(
            {
                position: 'topright',
                sidebar: this.sideBar(),
                text: '<i class="fa fa-info" aria-hidden="true"></i>'
            }
        );
        this.controls.info_btn = btn.addTo(this.map);
        $(btn._container).find('a').attr('i18n', 'map.control_moreinfo|title');
    },

    "show_message": function(text, parent) {
      if (arguments.length<2) parent = '#map';
      container = $(parent+' #sys_message');
      if (container.length==0) {
        container = $('<div>').attr('id', 'sys_message').addClass('btn').addClass('btn-block');
        $(parent).append(container);
      }
      container.attr('i18n', text);
      container.show();
      t().translate(MOSQUITO.lng, parent);
    },

    "hide_message": function(parent) {
      if (arguments.length==0) parent = '#map';
      $(parent+' #sys_message').hide();
    },

    addPanelDownloadControl: function(){
        var _this = this;
        var btn = new MOSQUITO.control.ControlDownload(
            {
                position: 'topright',
                sidebar: this.sideBar(),
                text: '<i class="fa fa-download" aria-hidden="true"></i>'
            }
        );
        this.controls.download_btn = btn;
        btn.on('download_btn_click', function(){
            var url = MOSQUITO.config.URL_PUBLIC + 'map_aux_reports_export.xls';
            url += '?bbox=' + this._map.getBounds().toBBoxString();
            if(_this.filters.year !== null){
                url += '&year=' + _this.filters.year;
            }
            if(_this.filters.months.length > 0){
                url += '&months=' + _this.filters.months.join(',');
            }
            // get categories to fetch
            layers = _this.controls.layers_btn.getSelectedKeys();

            categories = [];
            for (i=0 ; i< layers.length; ++i) {
              for (j=0 ; j < _this.LAYERS_CONF.length ; ++j) {
                if (_this.LAYERS_CONF[j].key == layers[i]) {
                  for (var category in _this.LAYERS_CONF[j].categories) {
                    categories =  categories.concat(_this.LAYERS_CONF[j].categories[category]);
                  }
                }
              }
            }
            // remove hashes
            for (i=0  ; i < categories.length ; ++i) {
                while (categories[i].indexOf('#')>-1) categories[i] = categories[i].replace('#','_');
            }

            url += '&categories=' + categories.join(',');
            window.location = url;
        });

        if (MOSQUITO.app.headerView.logged) {
            btn.addTo(_this.map);
            $(btn._container).find('a').attr('i18n', 'map.control_download|title');
            window.t().translate(MOSQUITO.lng, $(btn._container));
            window.t().translate(MOSQUITO.lng, $('.sidebar-control-download'));
        }

        MOSQUITO.app.on('app_logged', function(e){
            if(e === true){
                if(_this.controls.download_btn._map === undefined){
                    btn.addTo(_this.map);
                    $(btn._container).find('a').attr('i18n', 'map.control_download|title');
                    window.t().translate(MOSQUITO.lng, $(btn._container));
                    window.t().translate(MOSQUITO.lng, $('.sidebar-control-download'));
                }
            }else{
                if(_this.controls.download_btn._map !== undefined){
                    btn.removeFrom(_this.map);
                }
            }
        });
        //button on/off
        MOSQUITO.app.on('cluster_drawn', function(e){
            var btn_disabled = (e.n <= 0 )?true:false;
            $('.download_button button').attr('disabled', btn_disabled);
            if (btn_disabled) _this.show_message('error.no_points_selected', '.download_button');
            else _this.hide_message('.download_button');
        });

    },

    addReportsDocumentControl: function(){
        var _this = this;
        var btn = new MOSQUITO.control.ReportsDocumentControl(
            {
                position: 'topright',
                sidebar: this.sideBar(),
                text: '<i class="fa fa-share" aria-hidden="true"></i>'
            }
        );
        //button reportsdocument on/off
        MOSQUITO.app.on('cluster_drawn', function(e){
            var btn_disabled = (e.n > MOSQUITO.config.maxPrintReports || e.n == 0 )?true:false;
            $('#button-reportsdocument-tpl').attr('disabled', btn_disabled);
            if (btn_disabled) {
              if (e.n == 0) _this.show_message('error.no_points_selected', '.viewreports_button');
              else _this.show_message('error.too_many_points_selected', '.viewreports_button');
            } else _this.hide_message('.viewreports_button');
        });

        btn.on('reportsdocument_btn_click', function(){
            var url = '#/' + $('html').attr('lang') + '/reportsdocument/';
            url += _this.map.getBounds().toBBoxString();

            if(_this.filters.year === null){
                url += '/all';
            }else{
                url += '/' + _this.filters.year;
            }

            if(_this.filters.months.length === 0){
                url += '/all';
            }else{
                url += '/' + _this.filters.months.join(',');
            }

            // get categories to fetch
            layers = _this.controls.layers_btn.getSelectedKeys();
            categories = [];
            for (i=0 ; i< layers.length; ++i) {
              for (j=0 ; j < _this.LAYERS_CONF.length ; ++j) {
                if (_this.LAYERS_CONF[j].key == layers[i]) {

                  for (var category in _this.LAYERS_CONF[j].categories) {
                    categories =  categories.concat(_this.LAYERS_CONF[j].categories[category]);
                  }
                }
              }
            }
            // remove hashes
            for (i=0  ; i < categories.length ; ++i) {
                while (categories[i].indexOf('#')>-1) categories[i] = categories[i].replace('#','_');
            }
            url += '/' + categories.join(',');
            window.open(url);
        });
        this.controls.reportsdocument_btn = btn.addTo(this.map);
        $(btn._container).find('a').attr('i18n', 'map.control_viewreports|title');
    },

    addPanelShareControl: function(){
        var _this = this;
        var btn = new MOSQUITO.control.ControlShare(
            {
                position: 'topright',
                text: '<i class="fa fa-share-alt" aria-hidden="true"></i>',
                style: 'share-control',
                build_url: function(){
                    var layers = [];
                    $('.sidebar-control-layers ul > li.list-group-item').each(function(i, el){
                        if($(el).hasClass('active')){
                            if (!MOSQUITO.app.headerView.logged) {
                                layers.push(MOSQUITO.config.layers[i].key);
                            }
                            else{
                                layers.push(MOSQUITO.config.logged.layers[i].key);
                            }
                            // layers.push(i+'');
                        }
                    });
                    // find out any layer missing on the public layer list
                    var l = 0; var missing = [];
                    while (l < layers.length) {
                      var i = 0; var found = false;
                      while (i < MOSQUITO.config.layers.length && !found) {
                        if (MOSQUITO.config.layers[i].key.indexOf(layers[l].substring(0,1)) == -1) ++i;
                        else found = true;
                      }
                      if (!found) missing[missing.length] = layers[l];
                      ++l;
                    }
                    if (missing.length > 0) {
                      missingLayers = [];
                      for (i = 0; i < missing.length; ++i) {
                        pos = _this.getLayerPositionFromKey(missing[i]);
                        lay = $('.sidebar-control-layers ul > li.list-group-item:nth-child('+(pos+1)+')');
                        missingLayers.push(lay.html());
                      }

                      txt = t('share.private_layer_warn');
                      txt = txt.replace('()', '<ul><li>'+missingLayers.join('</li><li>')+'</li></ul>');
                      $('#control-share .warning').html('<div>'+txt+'</div>');
                    } else {
                      $('#control-share .warning').html('');
                    }

                    //$lng/$zoom/$lat/$lon/$layers/$year/$months
                    var url  = document.URL.replace(/#.*$/, '');
                    // if(url[url.length-1] !== '/'){
                    //     url += '/';
                    // }
                    url += '#';
                    url += '/' + document.documentElement.lang;

                    //if show report, center url in the report.
                    //report_id
                    if(_this.scope.selectedMarker !== undefined &&
                        _this.scope.selectedMarker !== null){
                            url += '/19' ;//fixed zoom when reporting
                            url += '/' + _this.scope.selectedMarker._latlng.lat;
                            url += '/' + _this.scope.selectedMarker._latlng.lng;
                    }
                    else{
                        url += '/' + _this.map.getZoom();
                        url += '/' + _this.map.getCenter().lat;
                        url += '/' + _this.map.getCenter().lng;
                    }
                    url += '/' + layers.join();

                    if(_this.filters.year === null){
                        url += '/all';
                    }else{
                        url += '/' + _this.filters.year;
                    }

                    if(_this.filters.months.length === 0){
                        url += '/all';
                    }else{
                        url += '/' + _this.filters.months.join(',');
                    }

                    //report_id
                    if(_this.scope.selectedMarker !== undefined &&
                        _this.scope.selectedMarker !== null){
                        url += '/' + _this.scope.selectedMarker._data.id;
                    }

                    return url;

                }
            }
        );

        this.controls.share_btn = btn.addTo(this.map);
        //$(btn._container).find('a').attr('i18n', 'map.control_share|title');

        // var input_share = $('#control-share .content .share_input');
        // var set_url = function(){
        //     var url = btn.build_url();
        //     var oldUrl = input_share.val();
        //     if(_this.scope.selectedMarker !== undefined &&
        //         _this.scope.selectedMarker !== null){
        //         url += '/' + _this.scope.selectedMarker._data.id;
        //     }
        //     if(oldUrl !== url){
        //         input_share.val(url).trigger('change');
        //     }
        // };

        // input_share.on('change', set_url);
        this.report_panel.on('show', function(){
            btn.set_url.call(btn);
        });
        this.report_panel.on('hide', function(){
            btn.set_url.call(btn);
        });

        this.filters.on('changed', function(){
            btn.set_url.call(btn);
        });

    },

    addPanelReport: function(){
        var _this = this;
        this.report_panel = $('<div>')
          .attr('class', 'sidebar-report');

        this.controls.sidebar.addPane(this.report_panel);

        this.report_panel.on('show', function(){
            if (_this.scope.selectedMarker){
                _this.markerSetSelected(_this.scope.selectedMarker);
            }
            else{
                //hide panel
            }
        });

        this.report_panel.on('hide', function(){
            if(_this.scope.selectedMarker !== undefined && _this.scope.selectedMarker !== null){
                _this.markerUndoSelected(_this.scope.selectedMarker);
            }
        });

        MOSQUITO.app.on('cluster_drawn', function(){

            if(_this.scope.selectedMarker !== undefined &&
                _this.scope.selectedMarker !== null){
                var found = _.find(_this.layers.layers.mcg.getLayers(), function(layer){
                    if(layer._data.id === _this.scope.selectedMarker._data.id &&
                        _this.map.hasLayer(layer)
                    ){
                        return layer;
                    }
                });

                if(found !== undefined){
                    _this.markerSetSelected(found);
                }else{
                    _this.markerUndoSelected(_this.scope.selectedMarker);

                    //search inside clusters

                    var cluster = _.find(_this.layers.layers.mcg._featureGroup._layers, function(layer){
                        if ( '_group' in layer){
                            // search marker inside clusters
                            var marker = _.find(layer._markers, function(m){
                                if ( m._data.id === _this.scope.selectedMarker._data.id ) {
                                    return m;
                                }
                            })

                            if(marker !== undefined){
                                layer.spiderfy();
                                _this.markerSetSelected(marker);
                                marker.fireEvent('click',{latlng:[0,0]});//latlng required for fireEvent
                                //return layer;
                            }
                        }
                    })
                }
            }
        });
    },

    //TODO: S'ha de posar en una vista
    show_report: function(marker){
        var nreport = _.clone(marker._data);
        //console.debug(nreport);

        if(nreport.expert_validation_result !== null &&
            nreport.expert_validation_result.indexOf('#') !== -1){
            nreport.expert_validation_result = nreport.expert_validation_result.split('#');
        }

        if (nreport.category) {
            layerkey = this.getLayerKeyByMarkerCategory(nreport.category);
            pos = this.getLayerPositionFromKey(layerkey);
            icon = this.getIconUrl(nreport.category);
            //nreport.titol_capa = this.LAYERS_CONF[pos].title;
        }
        nreport.t_answers = null;
        nreport.s_answers = null;
        nreport.questions = null;
        // only logged users. Queries & answers
        if (MOSQUITO.app.headerView.logged)  {
            if(nreport.t_q_1 != ''){
                nreport.t_answers = [];
                nreport.questions = [];
                nreport.t_answers[0] = nreport.t_a_1;
                nreport.questions[0] = nreport.t_q_1;
                if (nreport.t_q_2 != ''){
                    nreport.t_answers[1] = nreport.t_a_2;
                    nreport.questions[1] = nreport.t_q_2;
                }
                if (nreport.t_q_3 != ''){
                    nreport.t_answers[2] = nreport.t_a_3;
                    nreport.questions[2] = nreport.t_q_3;
                }
            }
            if(nreport.s_q_1 != ''){
                nreport.s_answers = [];
                nreport.questions = [];
                nreport.s_answers[0] = nreport.s_a_1;
                nreport.questions[0] = nreport.s_q_1;
                if (nreport.s_q_2 != ''){
                    nreport.s_answers[1] = nreport.s_a_2;
                    nreport.questions[1] = nreport.s_q_2;
                }
                if (nreport.s_q_3 != ''){
                    nreport.s_answers[2] = nreport.s_a_3;
                    nreport.questions[2] = nreport.s_q_3;
                }
                if (nreport.s_q_4 != ''){
                    nreport.s_answers[3] = nreport.s_a_4;
                    nreport.questions[3] = nreport.s_q_4;
                }
            }

        }else{
            nreport.note = null;
        }

        if(nreport.observation_date !== null &&
            nreport.observation_date !== '' ){
                var theDate = new Date(nreport.observation_date);
                nreport.observation_date = theDate.getDate() + '-' + ( theDate.getMonth() + 1 ) + '-' + theDate.getFullYear();
        }

        this.controls.sidebar.closePane();

        if(!('content-report-tpl' in this.templates)){
            this.templates[
                'content-report-tpl'] = $('#content-report-tpl').html();
        }
        var tpl = _.template(this.templates['content-report-tpl']);

        this.report_panel.html('');
        a = new L.Control.SidebarButton();
        a.getCloseButton().appendTo(this.report_panel);

        this.report_panel.append(tpl(nreport));
        window.t().translate($('html').attr('lang'), this.report_panel);

        this.controls.sidebar.togglePane(this.report_panel, $('<div>'));

        $('#map-ui .close_button').on('click', function() {
            _this.controls.sidebar.closePane();
        });
    },

    loading: {

        show: function(pix){
            this.img = $('#ajax_loader');
            if(this.img.length === 0){
                this.img = $('<img>')
                    .attr('id', 'ajax_loader')
                    .attr('src', 'img/ajax-loader.gif')
                    .appendTo($('body'));
            }

            this.img.show().offset({
              left: pix.x + 20,//    e.originalEvent.pageX + 20,
              top: pix.y // e.originalEvent.pageY
            });

        },
        hide: function(){
            this.img.offset({left: 0, top: 0}).hide();
        }
    }

});
