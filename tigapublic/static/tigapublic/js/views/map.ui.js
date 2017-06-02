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

    addRoleFunctions: function() {
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
          if (!MOSQUITO.app.mapView.scope.notifying) $(pnl.el).find('span').eq(1).html('0');
        });
        MOSQUITO.app.on('cluster_drawn', function(e){
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

        var select_years = $('<select multiple>')
            .attr('class', 'years')
            .appendTo(filtersSection);




        $.each(years, function(i, year) {
            var opt = $('<option>', {
                value: year[0],
                i18n: year[1]})
              .text(year[1]).appendTo(select_years);

            if(_this.filters.years.length > 0 &&
                _this.filters.years.indexOf(year[0]) !== -1){

                opt.attr('selected', 'selected');
            }

        });

        if(_this.filters.years.length === 0){
            select_years.val('all');
        }

        select_years.data('pre', select_years.val());

        select_years.on('change', function(){
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
            var years = $(this).val();
            $(this).data('pre', $(this).val());
            if(years[0] === 'all'){
                years = [];
            }else{
                years =_.map(years, Number);
            }

            _this.filters.trigger('years_change', years);
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

        //Add hashtag filters<div class="input-append">
        var div_hashtag = $('<div/>', {'id':'hashtag_filters', 'class':'section filters'})
            .appendTo(container);

        div_hashtag.html(`
            <form onsubmit="return:false">
            <input id="hashtag_search_text" type="text" placeholder="#hashtag" value="">
              <button id="hashtag_button_search" type="submit"><i class="fa fa-search"></i></button>
              <button id="hashtag_button_trash" type="submit"><i class="fa fa-trash"></i></button>
              </form>`);
        $('#hashtag_button_search').click(function(){
            _this.filters.trigger('hashtag_change', $('#hashtag_search_text').val());
            return false;
        });
        $('#hashtag_button_trash').click(function(){
            $('#hashtag_search_text').val('')
            _this.filters.trigger('hashtag_change', '');
            return false;
        });

        // Notification filter only for registered users
        if (MOSQUITO.app.headerView.logged) {
            var div_notif = $('<div/>', {'id':'notif_filters', 'class':'section filters'})
                .appendTo(container);
            var title_notif = $('<div>', {'i18n':'observations.filters.title', "class": "title"})
                .appendTo(div_notif);
            var select_notifications = $('<select>').attr('class', 'notif_filter')
                .appendTo(div_notif);
            var notif_filter_all = $('<option>', {"value": "all", "i18n": "all_notifications", "selected": "selected"})
                .appendTo(select_notifications);
            var notif_filter_mine = $('<option>', {"value": "withmine", "i18n": "with_my_notifications"})
                .appendTo(select_notifications);
            var notif_filter_notmine = $('<option>', {"value": "withoutmine", "i18n": "without_my_notifications"})
                .appendTo(select_notifications);

            select_notifications.on('change', function(){
              switch ($(this).val()) {
                case 'all':
                  _this.filters.trigger('notif_change', false);
                break;
                case 'withmine':
                  _this.filters.trigger('notif_change', 1);
                break;
                case 'withoutmine':
                  _this.filters.trigger('notif_change', 0);
                break;
              }
            });
        }

        trans.on('i18n_lang_changed', function(){
          setTimeout(function(){
              select_years.selectpicker('refresh');
              select_months.selectpicker('refresh');
              if (MOSQUITO.app.headerView.logged) {
                select_notifications.selectpicker('refresh');
              }
          }, 0);
        });

    }
    ,
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
    }
    ,
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

    "addNotificationControl": function() {
      if (this.userCan('notification')) {
        var _this = this;
        // define button
        var control = new MOSQUITO.control.ControlNotification(
            {
                position: 'topright',
                sidebar: this.sideBar(),
                text: '<i class="fa fa-bell" aria-hidden="true"></i>',
                "map": "dos"
            }
        );
        control.map = this.map;
        // store button in the main object
        this.controls.notification = control;
        // add button to the map
        control.addTo(this.map);
        // do translations
        $(control._container).find('a').attr('i18n', 'map.control_notifications|title');
        window.t().translate(MOSQUITO.lng, $(control._container));

        // Define interactions

        // When clicking the "Select polygon" button, start the editing mode
        $('#notification_select_polygon_btn').on('click', function() {
            control.startPolygonSelection();
        });

        control.pane.on('hide',function(){
            control.resetControl();
            control.drawHandler._toolbars.draw.disable()
        });

        // When user finishes the polygon
        this.map.on('draw:created', function (e) {
          control.finishPolygonSelection(e);
        });

        // When clicking on the form anchor, open the modal
        $('#create_notification_btn').on('click', function() {
          control.openForm(this);
        });
        $('#notification_form').on('hidden.bs.modal', function () {
          control.resetControl();
        })
      }

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
            var url = MOSQUITO.config.URL_API + 'map_aux_reports_export.xls';
            //prepare params based on filters
            url += '?bbox=' + this._map.getBounds().toBBoxString();

            if(_this.filters.years.length > 0){
                url += '&years=' + _this.filters.years.join(',');
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

            //Add filters if exists and !=false(all selected), N otherwise
            url += '&notifications='+(('notif' in _this.filters && _this.filters.notif!==false)?_this.filters.notif:'N');
            //Add hashtag if exists, N otherwise
            if ('hashtag' in _this.filters && _this.filters.hashtag.trim()!=''){
              hashtag = _this.filters.hashtag.replace('#','');
              if (hashtag=='') hashtag='N'
            }
            else hashtag = 'N';
            url += '&hashtag='+hashtag;
            //console.log('the hashtag '+_this.filters.hashtag);

            window.location = url;

        });


        btn.addTo(_this.map);
        $(btn._container).find('a').attr('i18n', 'map.control_download|title');
        window.t().translate(MOSQUITO.lng, $(btn._container));
        window.t().translate(MOSQUITO.lng, $('.sidebar-control-download'));

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
                //text: '<i class="fa fa-share" aria-hidden="true"></i>'
                text: '<i class="fa fa-file-text-o" aria-hidden="true"></i>'
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

            if(_this.filters.years.length === 0){
                url += '/all';
            }else{
                url += '/' + _this.filters.years;
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

            //Add filters if exists and !=false(all selected)
            url += (('notif' in _this.filters)&&(_this.filters.notif!==false))?'/'+_this.filters.notif:'/N';
            //Add hastag if exists and !=''
            url += ('hashtag' in _this.filters)?((_this.filters.hashtag.length)?'/'+_this.filters.hashtag:'/N'):'/N';
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
                    //Get layers set to look for active layers
                    if (MOSQUITO.app.headerView.logged) {
                        //Accordion objects has list-group-item class
                        layersDiv = $('.sidebar-control-layers #div_observations ul > li.list-group-item');
                    }
                    else{
                        layersDiv = $('.sidebar-control-layers #div_observations ul > li.list-group-only-item');
                   }
                    layersDiv.each(function(i, el){
                        if($(el).hasClass('active')){
                            //Get position of selected layers
                            id = $(el).attr('id').replace('layer_','');
                            pos = _this.getLayerPositionFromKey(id);
                            if (!MOSQUITO.app.headerView.logged) {
                                layers.push(MOSQUITO.config.layers[pos].key);
                                $('#control-share .warning').html('');
                            }
                            else{
                                layers.push(MOSQUITO.config.logged.layers[pos].key);
                                txt = t('share.private_layer_warn');
                                $('#control-share .warning').html('<div>'+txt+'</div>');
                            }
                            // layers.push(i+'');
                        }
                    });

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
                            url += '/' + _this.scope.selectedMarker._latlng.lat.toFixed(4);
                            url += '/' + _this.scope.selectedMarker._latlng.lng.toFixed(4);
                    }
                    else{
                        url += '/' + _this.map.getZoom();
                        url += '/' + _this.map.getCenter().lat.toFixed(4);
                        url += '/' + _this.map.getCenter().lng.toFixed(4);
                    }
                    url += '/' + layers.join();

                    if(_this.filters.years === null){
                        url += '/all';
                    }else{
                        url += '/' + _this.filters.years;
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

        //New notification button

        if (MOSQUITO.app.headerView.logged && this.userCan('notification') ){
            var notif_btn = $('<button>')
                .attr('class', 'btn btn-success btn-block')
                .attr('id', 'new_notification_btn')

            notif_btn.append('<span i18n="map.notification_add"></span>');

            var notif_btn_container = $('<div>')
                .attr('class', 'new-notification-container')
            .append(notif_btn);

            $('#popup_expert_validated')
                .prepend(notif_btn_container);

            notif_btn.on('click', function(){
                MOSQUITO.app.mapView.scope.notificationSelected = [MOSQUITO.app.mapView.scope.selectedMarker];
                MOSQUITO.app.mapView.scope.notificationClientIds = [MOSQUITO.app.mapView.scope.selectedMarker._data.id];
                MOSQUITO.app.mapView.controls.notification.updateResults(MOSQUITO.app.mapView.scope.notificationClientIds,['oneUser']);
                MOSQUITO.app.mapView.controls.notification.openForm();
            });
        }
        //////////////////

        window.t().translate($('html').attr('lang'), this.report_panel);

        this.controls.sidebar.togglePane(this.report_panel, $('<div>'));

        $('#notif_selectpicker').selectpicker('refresh');
        $('#notif_selectpicker').on('change', function(){
            _this = this;

            $('.close-notification').remove();
            var notif = $(this).find("option:selected").val();
            $('.detailed_notif').hide();

            var close_div = $('<div>')
                .attr('class','close-notification');

            var i = $('<i>')
                .attr('class','fa fa-times')
                .attr('aria-hidden','true');

            close_div.append(i);
            $('#'+notif).prepend(close_div);

            close_div.click(function(e){
                $(e.target).parent().parent().hide();
                value = t('info.notifications');
                $('#notif_selectpicker').val($("#notif_selectpicker option:first").val(value));
                $('#notif_selectpicker').selectpicker('refresh')
            });

            $('#'+notif).show();

        });

        $('#map-ui .close_button').on('click', function(){
            _this.controls.sidebar.closePane();
        });
    },

    loading: {
        on: function(obj) {
          var tag = (typeof obj.attr('id') != 'undefined')?obj.attr('id'):'';

          this.container = $('#loading_container_'+tag);
          if (this.container.length === 0) {
              this.container = $('<div>')
                  .attr('id', 'loading_container_'+tag)
                  .addClass('loading_container');
              this.img = $('<img>')
                  .attr('id', 'ajax_loader')
                  .attr('src', 'img/ajax-loader.gif')
                  .appendTo(this.container);
          } else this.container.fadeIn();
          if (arguments.length > 0) {
            obj.css('position', 'relative');
            this.container.addClass('embedded');
            this.container.appendTo(obj);
          } else {
            this.container.removeClass('embedded');
            this.container.appendTo($('#map'));
          }
        },
        off: function(obj) {
          var tag = (typeof obj.attr('id') != 'undefined')?obj.attr('id'):'';
          this.container = $('#loading_container_'+tag);
          this.container.fadeOut();
        },
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
    },

    putStormDrainLegend: function(d){
      str='';

      //clusters same colors respecting user order definition
      d=d.categories;
      var rest = d.slice();
      var sorted=[];//Eventually sorted array of objects
      var colors=[] //array of included colors
      d.forEach(function (value, index, arr){
        var color = value.color;//Keep track of colors already read
        if (colors.indexOf(color)==-1) {
          colors.push(color);
          sorted.push(value)

          rest = rest.slice(1);
          tmp = rest.slice();
          tmp.forEach(function (v, i, a){
            if (v.color == color) {
              rest.splice(i,1)
              sorted.push(v);
            }
          })
        }
      })

      previousColor='';
      sorted.forEach(function(category, index, arr){

          svgContent = '<circle cx="10" cy="7" r="5" stroke="black" stroke-width="1" fill="'+category.color+'" />'
          str +=`<li class="stormdrain_legend">
          <div class="tr t-top">
            <div class="tcel t-top">
            <svg width="25px" height="20px" xmlns="http://www.w3.org/2000/svg">` + svgContent + `
            </svg>
            </div>`;

          conds = category.conditions;

          str+='<div class="tcel t-top">'
          str+='<div class="tt" style="border-top:1px">'

          conds.forEach(function(oneCondition, i, ar){
            str+='<div class="tr">'

            field = oneCondition.field;
            value = oneCondition.value;
            operator = ' ' + oneCondition.operator + ' ';
            //or, if translation
            operator_txt = 'stormdrain.operator-'+operator;
            field_txt = 'stormdrain.field-'+field;

            str+='<div class="tcel"><span i18n="'+field_txt+'"></span></div>';

            //translate value, only if there is a translation
            if (('stormdrain.value-'+value.toLowerCase()) in trans[MOSQUITO.lng]){
              val_txt = 'stormdrain.value-'+value.toLowerCase();
              str+='<div class="tcel">'+operator+'<span class="ml" i18n="'+val_txt+'"></span></div>';
            }
            else {
              str+='<div class="tcel"><span class="ml">' + operator +' '+value + '</span></div>';
            }


            str+='</div>'
          })

          str +='</div>';
          str +='</div></li>';

      })
      $('#stormdrain_legend').removeClass('sub-sites');
      $('#stormdrain_legend').html(str);
      //Evan new i19n attribs
      trans.trigger('i18n_lang_changed', MOSQUITO.lng);
    }
    ,
    //Make ajax call and prepare input, select and call stormDrainStyleUI to show style UI.
    stormDrainSetup:function(){
      //Ajax call to get params

      url = MOSQUITO.config.URL_API + 'getStormDrainUserSetup/';
      $.ajax({
          "async": true,
          "url": url,
          "datatype": 'json',
          "context": this
      }).done(function(data) {

          //Remove element and add them all over again
          $('.select-st-version').find('option').remove();
          myVersionsSelect = $('.select-st-version');

          //IF there is no versions, then emulate one
          if (Object.keys(data.versions).length==0){
            data.versions={
              '1':{
                    'title':'',
                    'date': new Date(),
                    'style_json': {
                        'categories':[{
                          'color':'#ff0000',
                          'conditions':[{'field':'water',
                                      'value':'true',
                                      'operator':'='}]
                          }]
                      },
                    'visible': true
                }};
          };

          $.each(data.versions, function(key, vContent) {
              var opt = $('<option>', {
                    value: key})
              .text(key+' '+vContent.title).appendTo(myVersionsSelect);

              //At leat one condition is necessary(water=true, red)
              if (vContent.style_json.categories[0].conditions.length  == 0){
                vContent.style_json.categories[0].conditions.push({"field":"water","value":"1","operator":"="});
              }

              if (vContent.visible==true) {
                  $(opt).attr('selected',true);
                  //Set style for first selected value
              }
            })

            users_versions={};

            //Check if extra users key exists
            if ('users_version' in data){

              //only first time modal is open
              if (! ('stormdrain_setup_events' in this)) {

                  versionValue = 1; //Version to show on UI. Superusers have only one version
                  //Prepare div to clone
                  parentDiv = $('.tr-user-version:first').closest('.tt');
                  contentDiv = $('.tr-user-version:first')

                  //Remove default select
                  $('select[name=select-st-version]').remove();
                  none_txt = t('stormdrain.none-txt');

                  $.each(data.users_version, function(iduser, obj) {
                    username = obj.username;
                    userVersions = obj.versions;
                    init_value = obj.visible;

                    u_txt = t('stormdrain.user-txt') +' '+username;

                    span = $('<span>')
                      .attr('i18n', 'stormdrain.user-txt')//when lang changes
                      .text(t('stormdrain.user-txt'));//first text

                    //$(span).appendTo(span1);

                    sel = $('<select>',{
                      id:iduser,
                      name:username,
                      class: 'a-user-version'
                    });
                    //First option to exclude one user from map
                    opt = $('<option>',{value:0, i18n: 'stormdrain.none-txt'}).text(none_txt);
                    if (init_value == '0'){
                      $(opt).attr('selected',true);
                    }
                    $(sel).append(opt);

                    userVersions.forEach(function(value, index, arr){
                      opt = $('<option>',{value:value.version})
                        .text(value.title.slice(0,30) +' ('+value.date+')');
                      if (value.version == init_value){
                        $(opt).attr('selected',true);
                      }
                      $(sel).append(opt);
                    })

                    userDiv = $(contentDiv).find('.users-name');
                    selectDiv = $(contentDiv).find('.users-select');

                    $(userDiv).html(span);//Replace cloned content
                    $(userDiv).html( $(userDiv).html() +' '+ username)
                    $(selectDiv).html(sel);
                    $(parentDiv).append(contentDiv);
                    contentDiv = $('.tr-user-version:last').clone();
                  })
                }
            }
            else{
              $('.select-st-version').attr('id', data.user);
              versionValue = $('.select-st-version').val();

            }

            if (Object.keys(data.fields).length==0) {
              alert('Upload data first');
              return true;
            }
            else{
              //Show modal
              $('#stormdrain_setup').modal('show');
            }

            if (! ('stormdrain_setup_events' in this)) {
                //Set Events only once
                this.stormDrainEvents(data);
                this.stormdrain_setup_events = true;
            }

            //SAVE Ajax Data in view
            this.stormdrain_setup = data;

            //If superadmin, get possible values
            if ('users_version' in this.stormdrain_setup){
              this.getPossibleFieldValues();
            }

            //Call default style setup
            this.stormDrainStyleUI(versionValue);

      });

    }
    ,
    //stormDrainStyleUI: function(version, fieldsData){
    stormDrainStyleUI: function(version){
      if (version) {
        //categories = JSON.parse(this.stormdrain_setup[version].style_json).data;
        categories = this.stormdrain_setup.versions[version].style_json.categories;

        //super users have different field values (mergins values of all users)
        if ('admin_values' in this.stormdrain_setup){
          fieldsData = this.stormdrain_setup.admin_values;
        }
        else {
          iduser = $('.select-st-version').attr('id');
          fieldsData = this.stormdrain_setup.fields[iduser][version];
        }

        operatorsData = this.stormdrain_setup.operators;
        maxConditions = Object.keys(fieldsData).length + 1;//Date type has 2 options >= & <=

        //before start, remove all categori boxes but last where add category button is
        $('.category-wrapper').not(':last').remove();

        //Also remove conditions but first
        categories.forEach(function(current, index, arr){

          color = current['color'];
          conds = current['conditions'];
          currentCategoryDiv = $('.category-wrapper:eq('+index+')');
          $(currentCategoryDiv).find('.category-values').not(':first').remove();
          $(currentCategoryDiv).find('input[type=color]').val(color);

          //Remove Add-condition button if it is not necessary
          if (maxConditions ==  1){
            $(currentCategoryDiv).find('.stormdrain-add-condition').hide();
          }

          conds.forEach(function(partialCondition, ind, a){
              nCreatedConds = $(currentCategoryDiv).find('.category-values').length;
              $(currentCategoryDiv).find('select[name=field]:last').find('option').remove();

              field = partialCondition.field;
              val = partialCondition.value;
              operator = partialCondition.operator

              //Fields selection
              selectField = $(currentCategoryDiv).find('select[name=field]:last');
              //Order text options
              keys = Object.keys(fieldsData);
              txts=[]
              keys.forEach(function(k, index, arr){
                txt = t('stormdrain.field-'+k);
                txts.push([txt, k]);
              })
              txts.sort();
              txts.forEach(function(t, index, arr){
                txt = t[0]; k =t[1];
                var opt = $('<option>', {
                    value: k
                  }).text(txt).appendTo(selectField);
              })

              $(selectField).val(field);

              //Insert the right options on select-operators based on selected select-field
              selectToCheck = $(currentCategoryDiv).find('select[name=operator]:last');
              $(selectToCheck).find('option').remove();
              possibleOptions = operatorsData[field];
              $.each(possibleOptions, function(i, value) {
                  txt = (('stormdrain.operator-'+value) in trans[MOSQUITO.lng])?t('stormdrain.operator-'+value):value;
                  var opt = $('<option>', {
                      value: value
                    }).text(txt).appendTo(selectToCheck);
                })

              $(currentCategoryDiv).find('select[name=operator]:last').val(operator);

              //Insert the right options on select-values based on selected select-field
              selectToCheck = $(currentCategoryDiv).find('select[name=value]:last');
              $(selectToCheck).find('option').remove();

              //if closest field is a date, then sort desc
              possibleOptions = fieldsData[field].sort();
              closestField = $(selectToCheck).closest('.tr.category-values').find('select[name=field]');
              if ($(closestField).val()=='date'){
                possibleOptions = possibleOptions.reverse();
              }

              $.each(possibleOptions, function(i, value) {
                  txt = (('stormdrain.value-'+value) in trans[MOSQUITO.lng])?t('stormdrain.value-'+value):value;
                  var opt = $('<option>', {
                      value: value
                    }).text(txt).appendTo(selectToCheck);
                })

              //Check if val exists within available options
              if ($('select[name=value]:last  option[value="'+val+'"]').length > 0){
                $(currentCategoryDiv).find('select[name=value]:last').val(val);
              }
              else{
                $(currentCategoryDiv).find('select[name=value]:last').find('option:first').attr('selected','true');
              }

              if (conds.length > nCreatedConds){
                //Trigger just last "+" button (that is, just on last category)
                $('.stormdrain-add-condition:last').trigger('click');
              }
          })
          //check if add-condition button is necessary
          if (maxConditions < conds.length){
            $(currentCategoryDiv).find('.stormdrain-add-condition').hide();
          }
          ncategories = $('.category-wrapper').length;

          if (categories.length > ncategories){
            $('.category-add:last').trigger('click');
          }
        })
      }
    }
    ,
    stormDrainEvents : function(ajaxData){
      _this = this;

      // Show additional help
      $('#helper-text .display_example').on('click', function() {
        $('#stormdrain_setup_example').modal('show');
      });

      //Some add/cancel buttons stuff
      //SUBMIT event
      $('.stormdrain-submit').on('click', function(){
          //Create json structure

          //Get category params, version, color params, condition params
          params={'version_data':0, 'categories':[]};
          categories = $('.category-wrapper');
          $.each(categories, function(i,category){
            color = $(this).find('.color').val();

            params['categories'].push({'color':color, 'conditions':[]});

            conditions = $(this).find('.category-values');
            //To avoid repeated conditions inside same category
            stringifiedConditions = '';
            $.each(conditions, function(j,condition){
                field = $(this).find('.stormdrain_field').val();
                value = $(this).find('.stormdrain_value').val();
                operator = $(this).find('.stormdrain_operator').val();
                if ( (field !==null && value!==null) && (field !='' && value!='')  ){
                  newCondition={
                    'field' : field,
                    'value' : value,
                    'operator' : operator
                  }
                  if (stringifiedConditions.indexOf(JSON.stringify(newCondition)) == -1){
                    params['categories'][i]['conditions'].push(newCondition);
                  }
                  stringifiedConditions += JSON.stringify(newCondition);

                }
              });
          });

          //if super-userCheck users version
          if ($('select.a-user-version').length){
            users_v=[]
            all = $('select.a-user-version');
            $.each(all, function(i,one){
              user_id = $(one).attr('id');
              username = $(one).attr('name');
              v = $(one).val();

              one_v ={"username": username, "user_id": user_id, "version": v}
              users_v.push(one_v);
            })
            params['users_version'] = users_v;
            params['version_data'] = 1; //Super users have only version = 1


          } else{
            params['version_data'] = $('.select-st-version').val();
          }
          //SAVE style Ajax
          $.ajax({
              url:  MOSQUITO.config.URL_API + 'put/style/version/',
              type: 'POST',
              //data: params,
              data: JSON.stringify(params),
              contentType: "application/json; charset=utf-8",
              context: this,
              success: function(result) {
                  //Load layer even if it wasn't loaded
                  if (result.success){
                    _this.loadStormDrainData(true);
                    $('#layer_Q').addClass('active');
                    $('.stormdrain-submit-ok').show();
                    setTimeout(function(){
                        //hide elements
                        $('.stormdrain-submit-ok').hide();
                        $('#stormdrain_setup').modal('hide');
                    }, 2000);
                  }
                  else{
                    $('.st-setup-err').html(result.err);
                    $('.st-setup-err').show();
                    setTimeout(function(){
                        //hide elements
                        $('.st-setup-err').hide();
                        $('#stormdrain_setup').modal('hide');
                    }, 2000);
                  }

              }
          });

      })

      //When select version changes, show style for new version
      $('.select-st-version').on('change', function(){
        val = $(this).val();
        _this.stormDrainStyleUI(val);
      })

      //When field selected,then search for its values
      $('.stormdrain_field').on('change',function(){
          //remove all options and add the good ones
          fieldName = $(this).val();
          //Super users do not have select-st-version choice
          version = ($('.select-st-version').length)?$('.select-st-version').val():1;

          //Select-Values
          myValuesSelect = $(this).parent().siblings().find('.stormdrain_value');
          $(myValuesSelect).find('option').remove();
          iduser =_this.stormdrain_setup.user;
          //super users have different field values
          if ('admin_values' in _this.stormdrain_setup){
            options = _this.stormdrain_setup.admin_values[fieldName];
          }
          else {
            options = _this.stormdrain_setup.fields[iduser][version][fieldName];
          }

          $.each(options, function(i, option) {
            txt = (('stormdrain.value-'+option) in trans[MOSQUITO.lng])?t('stormdrain.value-'+option):option;
              var opt = $('<option>', {
                  value: option,
                  })
                .text(txt).appendTo(myValuesSelect);
            })
            //Select-Operators
            myOperatorsSelect = $(this).parent().siblings().find('.stormdrain_operator');
            $(myOperatorsSelect).find('option').remove();
            options = _this.stormdrain_setup.operators[fieldName];
            $.each(options, function(i, option) {
              txt = (('stormdrain.operator-'+option) in trans[MOSQUITO.lng])?t('stormdrain.operator-'+option):option;
                var opt = $('<option>', {
                    value: option,
                    })
                  .text(txt).appendTo(myOperatorsSelect);
              })
      })

      //Add condition event
      $('.stormdrain-add-condition').on('click',function(){
        //Super users do not have seletc-st-version choice
        version = ($('.select-st-version').length)?$('.select-st-version').val():1;

        parentDiv = $(this).closest('.category-conditions');

        //check if there is room for another condition
        numCurentConditions = $(parentDiv).find('.category-values').length;

        iduser =_this.stormdrain_setup.user;
        if ('admin_values' in _this.stormdrain_setup){
          maxConditionsAllowed = Object.keys(_this.stormdrain_setup.admin_values).length + 1;//Date field can hold 2 conditions
        }
        else{
          maxConditionsAllowed = Object.keys(_this.stormdrain_setup.fields[iduser][version]).length + 1;//Date field can hold 2 conditions
        }


        _originalButton = this;

        if (numCurentConditions < maxConditionsAllowed)
        {
          cloneFrom = $(parentDiv).find('.category-values:first');
          cloneDiv = $(cloneFrom).clone(true);
          //$(cloneDiv).find('input').remove();
          $(parentDiv).append(cloneDiv);
          $(cloneDiv).find('select[name=field]:last').trigger('change');

          //Add - button to remove condition
          button = $('<button>').html('<i class="fa fa-trash"></i>');
          $(cloneDiv).find('.tcel:last').append(button);

          //if ( $(parentDiv).find('.category-values').length >= maxConditionsAllowed ){
            //$(cloneDiv).closest('.category-wrapper').find('.stormdrain-add-condition').hide();
          //}

          //Add cancel category event
          $(button).on('click', function(){
            //do not remove, before show. Order is mandatory
            $(this).closest('.category-conditions').find('.stormdrain-add-condition').show();
            $(this).closest('.category-values').remove();
          })
          //Now that there is one more condition, check if another one is possible
          if ( !((numCurentConditions + 1) < maxConditionsAllowed)){
            $(this).hide();
          }
        }
        else{
          //Remove add-condition button
          $(this).hide();
        }


      })

      //Add category
      $('.category-add').on('click', function(){

        cloneFrom = $(this).closest('.category-wrapper');
        //Remove all conditions but first ones, add-condition button visible
        cloneDiv = $(cloneFrom).clone(true);
        $(cloneDiv).find('.category-values').not(':first').remove();
        $(cloneDiv).find('.category-headers').find('.stormdrain-add-condition').show();
        $(cloneDiv).find('select[name=field]:last').trigger('change');

         //change button on cloneFrom div and prepare click event
        cancelButton = $('<button>')
          .attr('class', 'category-cancel')
          .html('<i class="fa fa-trash"></i>');
        $(cloneFrom).find('.t-addcategory').html(cancelButton);
        _initialButton = this;
        $(cancelButton).on('click', function(){
          cloneDiv = $(this).closest('.category-wrapper').remove();
          //then again, show add-condition button
          $(_initialButton).show();
        })

        //Finally add new category box
        $('.categories-container').append(cloneDiv);
      })

      //Add events for all a-user-version selects (only for superusers)
      $('.a-user-version').on('change', function(){
        //At least one select must be != 0
        var atLeastOne = false;
        $.each($('select.a-user-version'), function(i, sel) {
            if ($(sel).val()!='0') atLeastOne = true;
        })

        if (atLeastOne){
          //merge distinct values of selected users and versions
          _this.getPossibleFieldValues();
          _this.stormDrainStyleUI(1); //admin users have stormdrain data of their own
        }
        else{
          //Select first option <> 0
          var v = $('select.a-user-version:first').find('option:eq(1)').val();
          $('select.a-user-version:first').val(v);
        }
      })
    },

    getPossibleFieldValues: function(){
      _this = this;
      this.stormdrain_setup.admin_values={};
      var distinctValues={}

      $.each($('select.a-user-version'), function(i, value) {
        id = $(value).attr('id');
        ver = $(value).val();
        if (ver != '0'){
          thisUserValues = this.stormdrain_setup.fields[id][ver];
          for (var key in thisUserValues) {
            if (key in distinctValues){
              //add only the new values
              //distinctValues[key]=[];
              thisUserValues[key].forEach(function(val, i, arr){
                if (distinctValues[key].indexOf(val)==-1){
                  distinctValues[key].push(val);
                }
              })
            }
            else{
              distinctValues[key] = thisUserValues[key].slice();
            }
          }
        }
      }.bind(this))
      this.stormdrain_setup.admin_values = distinctValues;
    }
    ,

    stormDrainResetUpload: function(){
      $('#stormDrainUpload').find('.selected-file-name').val('');
      $('#stormDrainUpload').find('#stormdrain-upload-file').val('');
      $('input[name=stormdrain-title').val('');

      $('.upload-step1').show();
      $('#stormDrainUpload').find('.st-upload-error').hide();
      $('#stormDrainUpload').find('.stormdrain-import-started').hide();
      $('#stormDrainUpload').find('.stormdrain-import-finished').hide();
      $('#stormDrainUpload').find('.progress-bar-wrapper').hide();
      $('#stormDrainUpload').find('.stormdrain-upload-submit').show();
      $('#stormDrainUpload').find('.button-file').show();
      $('#stormDrainUpload').find('.stormdrain-upload-submit').show();
      $('#stormDrainUpload').find('.progress-bar-info').css('width','0%');
    }

    ,

    stormDrainUploadEvents: function(){
      //Get template button
      $('.btn-st-template').on('click', function(){
        var url = MOSQUITO.config.URL_API + 'stormdrain/get/template/';
        window.location = url;
      })

      //Customized input file button
      $('#stormdrain-upload-file').on('change', function(){
          var input = $(this);
          label = input.val().replace(/\\/g, '/').replace(/.*\//, '');

          var input = $(this).parents('.input-group').find(':text'),
              log = label;

          if( input.length ) {
              input.val(log);
          } else {
              if( log ) alert(log);
          }
      });

      $('#stormdrain-upload-file').on('change', function(){
        //hide potencially visible errors
        $('.st-upload-error').hide();
      })


      $('.btn-st-setup-now').on('click', function(){
          //close upload modal
          $('#stormdrain_upload').modal('hide');
          //trigger modal setup
          $('.fa-cog.storm_drain').trigger('click');

      })

      $('.btn-st-setup-later').on('click', function(){
          $('#stormdrain_upload').modal('hide');
      })

      $('.stormdrain-upload-submit').click(function(e){
        //submit function
        function stormDrainUploadSubmit(callback){
          var form = $('form#stormDrainUpload')[0];
          var formData = new FormData(form);
          $('.progress-bar-wrapper').show();
          formData.append("title", $('input[name=stormdrain-title]').val());

          $.ajax({
              type: "POST",
              enctype: 'multipart/form-data',
              url: MOSQUITO.config.URL_API +'fileupload/',
              data: formData,
              processData: false,
              //contentType: false,
              contentType: 'multipart/form-data',
              cache: false,

              xhr: function() {
                  var xhr = $.ajaxSettings.xhr();
                  if (xhr.upload) {
                      xhr.upload.addEventListener('progress', function(evt) {
                          var percent = ((evt.loaded / evt.total) * 100).toFixed(2);
                          $(".progress-bar").html(percent+ "%");
                          $(".progress-bar").width(percent + "%");
                          if (evt.loaded == evt.total){
                              $('.upload-step1').hide();
                              $('.stormdrain-import-started').show();
                          }
                      }, false);
                  }
                  return xhr;
              },
              success: function(data) {
                //hide/show stuff
                $('.st-upload-error').hide();
                $('#stormDrainUpload').find('.stormdrain-upload-submit').hide();
                $('#stormDrainUpload').find('.stormdrain-import-started').hide();
                $('#stormDrainUpload').find('.button-file').hide();
                $('#stormDrainUpload').find('.progress-bar-wrapper').hide();

                if (data.success){
                  $('#stormDrainUpload').find('.stormdrain-import-finished').show();
                }
                else{
                  txt_error = t('stormdrain.upload-error') + '<br/>' + data.err;
                  $('#stormDrainUpload').find('.st-upload-error').html(txt_error);
                  $('#stormDrainUpload').find('.st-upload-error').show();
                }


              },
              error: function() {
                $('.stormdrain-import-started').hide();
                $('.stormdrain-import-finished').hide();
                $('#stormDrainUpload').find('.stormdrain-upload-submit').hide();
                $('#stormDrainUpload').find('.progress-bar-wrapper').hide();
                $('.st-upload-error').html('Error')
                $('.st-upload-error').show();
              },
              data: formData,
              cache: false,
              contentType: false,
              processData: false
          }, 'json');
        }

        val = $('#stormdrain-upload-file').val();
        tit = $('input[name=stormdrain-title]').val();
        if (val.length && tit.length){
          $('.st-upload-error').hide();
          //do submit
          stormDrainUploadSubmit()
        }
        else{
          $('.st-upload-error').html(t('stormdrain.upload-required'));
          $('.st-upload-error').show();
        }
      })
    }
    ,
    stormDrainUploadSetup: function(){
      _this = this;
      //Reset form just in case it was opened before
      this.stormDrainResetUpload();
      if (! ('stormdrain_upload_events' in this)){
          url = MOSQUITO.config.URL_API + 'getStormDrainUserSetup/';
          $.ajax({
              "async": true,
              "url": url,
              "datatype": 'json',
              "context":this
          }).done(function(data) {
              //Remove element and add them all over again
              $('.select-st-version').find('option').remove();
              myVersionsSelect = $('.select-st-version');

              versions={};
              $.each(data.versions, function(i, version) {
                  //All version properties
                  versions[version[0]]={
                      'published_date':version[1],
                      'style_json':version[2],
                      'visible':version[3]
                  }
              })
              this.stormdrain_versionsData = versions;
              if (! ('stormdrain_upload_events' in this)) {
                //Set Events only once
                  this.stormDrainUploadEvents();
                  this.stormdrain_upload_events = true;
              }


              $('.new-version-value').text(data.versions.length + 1);
        })
      }
      else{
          $('.new-version-value').text(Object.keys(this.stormdrain_versionsData).length +1 );
      }

      $('#stormdrain_upload').modal('show');
    }
});
