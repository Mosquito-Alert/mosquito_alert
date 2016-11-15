var MapView = MapView.extend({

    addZoomControl: function(){
        this.controls.zoom = new L.Control.Zoom(
            {position: 'topright'}).addTo(this.map);
    },

    sideBar: function(){
        if(typeof(this.controls.sidebar) === 'undefined'){
            this.controls.sidebar = L.OSM.sidebar('#map-ui')
                .addTo(this.map);
            this.map.on('click', function(){
                this.controls.sidebar.closePane();
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
            layers[i].icon = this.getIconUrl(key);
        }

        var btn = new MOSQUITO.control.ControlLayers(
            {
                position: 'topright',
                sidebar: this.sideBar(),
                active: true,
                layers: layers,
                text: '<i class="fa fa-bars" aria-hidden="true"></i>'/*,
                title: t('map.control_layers')*/
            }
        );
        this.controls.layers_btn = btn.addTo(this.map);
        $(btn._container).find('a').attr('i18n', 'map.control_layers|title');

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
            //url += '&excluded_types=' + _this.filters.excluded_types.join(',');
            if(_this.filters.year !== null){
                url += '&year=' + _this.filters.year;
            }
            if(_this.filters.months.length > 0){
                url += '&months=' + _this.filters.months.join(',');
            }
            window.location = url;
        });

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
                            layers.push(i+'');
                        }
                    });

                    //$lng/$zoom/$lat/$lon/$layers/$year/$months
                    var url  = document.URL.replace(/#.*$/, '');
                    // if(url[url.length-1] !== '/'){
                    //     url += '/';
                    // }
                    url += '#';
                    url += '/' + document.documentElement.lang;
                    url += '/' + _this.map.getZoom();
                    url += '/' + _this.map.getCenter().lat;
                    url += '/' + _this.map.getCenter().lng;
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
        $(btn._container).find('a').attr('i18n', 'map.control_share|title');

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
            _this.markerSetSelected(_this.scope.selectedMarker);
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
                }
            }
        });

    },

    addReportsDocumentControl: function(){
        var _this = this;
        var btn = new MOSQUITO.control.ReportsDocumentControl(
            {
                position: 'topright',
                text: '<i class="fa fa-share" aria-hidden="true"></i>',
                style: 'reports-button'
            }
        );
        //TODO: agafar l'idioma dde l'aplicació
        btn.on('click', function(){
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

            if(_this.filters.excluded_types.length === 0){
                url += '/none';
            }else{
                url += '/' + _this.filters.excluded_types.join(',');
            }



            //this.filters = {year: null, months: [], excluded_types: []};
            //url += '/' + _this.controls.layers_btn.getSelectedKeys().join(',');
            window.open(url);
        });
        this.controls.reportsdocument_btn = btn.addTo(this.map);
        //$(btn._container).find('a').attr('i18n', 'map.control_share|title');


    },

    //TODO: S'ha de posar en una vista
    show_report: function(marker){
        var nreport = _.clone(marker._data);
        //console.debug(nreport);
        if(nreport.expert_validation_result !== null &&
            nreport.expert_validation_result.indexOf('#') !== -1){
            nreport.expert_validation_result = nreport.expert_validation_result.split('#');

            nreport.expert_validation_result_specie = nreport.expert_validation_result[0];
            if ( nreport.expert_validation_result_specie == 'site'){
                nreport.titol_capa = 'site';
            } else if ( nreport.expert_validation_result[1] == 1 ) {
                nreport.titol_capa = nreport.expert_validation_result_specie +'_posible';
            } else if (nreport.expert_validation_result[1] == 2){
                nreport.titol_capa = nreport.expert_validation_result_specie +'_confirmado';
            } else if (nreport.expert_validation_result[1] == 0){
                nreport.titol_capa = 'unidentified';
            } else{
                nreport.titol_capa = 'other_species';
            }
        }

        if(nreport.mosquito_answers !== null &&
            nreport.mosquito_answers.indexOf('#') !== -1){
            nreport.mosquito_answers = nreport.mosquito_answers.split('#');
        }

        if(nreport.observation_date !== null &&
            nreport.observation_date !== '' ){
                var theDate = new Date(nreport.observation_date);
                nreport.observation_date = theDate.getDay() + '-' + ( theDate.getMonth() + 1 ) + '-' + theDate.getFullYear();
        }

        this.controls.sidebar.closePane();

        if(!('content-report-tpl' in this.templates)){
            this.templates[
                'content-report-tpl'] = $('#content-report-tpl').html();
        }
        var tpl = _.template(this.templates['content-report-tpl']);
        this.report_panel.html(tpl(nreport));
        window.t().translate($('html').attr('lang'), this.report_panel);

        this.controls.sidebar.togglePane(this.report_panel, $('<div>'));

    },

    loading: {
        show: function(e){
            this.img = $('#ajax_loader');
            if(this.img.length === 0){
                this.img = $('<img>')
                    .attr('id', 'ajax_loader')
                    .attr('src', 'img/ajax-loader.gif')
                    .appendTo($('body'));
            }
            this.img.show().offset(
                {left: e.originalEvent.pageX + 20, top: e.originalEvent.pageY});

        },
        hide: function(){
            this.img.offset({left: 0, top: 0}).hide();
        }
    }

});
