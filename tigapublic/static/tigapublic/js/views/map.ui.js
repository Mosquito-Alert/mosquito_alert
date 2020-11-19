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
                    if (_this.lastViewWasReload === false){
                        this.load_data();
                    }
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
          if ('mapView' in MOSQUITO.app && !MOSQUITO.app.mapView.scope.notifying) $(pnl.el).find('span').eq(1).html('0');
        });
        MOSQUITO.app.on('cluster_drawn', function(e){
            $(pnl.el).find('span').eq(1).html(e.n);
        });

    },

    newFilterGroup:function(params) {
      if (typeof params.id == 'undefined') {
        if (console && console.error) console.error('map.ui.newFilterGroup requires and object with an ID attribute.');
        return false;
      }

      return $('<div/>', {
        'id': params.id,
        'class':'section filters',
        "i18n": params.title+'|title'
      });
    },

    addTimeFiltersTo: function(section) {
      var _this = this;
      // Setup Years
      var years = [ ['all', t('All years')] ];
      var current_year = new Date().getFullYear();
      for(var i = 2014; i <= current_year; i++){
          years.push([i,i]);
      }
      // Create time group
      var div_time = this.newFilterGroup({
        'id': 'time_group',
        'title': 'group.filters.time'
      });

      if (div_time) div_time.appendTo(section);
      // Create year select
      var select_years = $('<select multiple>')
          .attr('class', 'years')
          .attr('id', 'select_years')
          .appendTo(div_time);
      // Add options to year select
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
      // Select the 'all' option if none is used
      if(_this.filters.years.length === 0){
          select_years.val('all');
      }
      // Store the current value in the HTML
      select_years.data('pre', select_years.val());
      // Year Change event
      select_years.on('change', function(){
          var pre = $(this).data('pre');
          var now = $(this).val();
          if(pre.indexOf('all') !== -1){
              var newdata = $(this).val();
              if(newdata!==null){
                  newdata.shift();
                  $(this).val(newdata);
                  _this.activeFilterBackground(this);
                  calendar_input.daterangepicker('clearRange');
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
              _this.deactiveFilterBackground(this);
          }else{
              years =_.map(years, Number);
          }

          _this.filters.trigger('years_change', years);
      });
      // Define months
      var months = [
        ['all', t('All months')],
        ['1', t('January')], ['2', t('February')], ['3', t('March')],
        ['4', t('April')], ['5', t('May')], ['6', t('June')],
        ['7', t('July')], ['8',t('August')], ['9', t('September')],
        ['10', t('October')], ['11', t('November')],
        ['12', t('December')]
      ];
      // Create month select
      var select_months = $('<select multiple>')
            .attr('class', 'months')
            .attr('id', 'select_months')
            .appendTo(div_time);
      // Add options to month select
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
      // Select the 'all' option if none is used
      if(_this.filters.months.length === 0){
          select_months.val('all');
      }
      // Store the current value in the HTML
      select_months.data('pre', select_months.val());
      // Month Change event
      select_months.on('change', function(){
          var pre = $(this).data('pre');
          var now = $(this).val();
          if(pre.indexOf('all') !== -1){
              var newdata = $(this).val();
              if(newdata!==null){
                  newdata.shift();
                  $(this).val(newdata);
                  _this.activeFilterBackground(this);
                  calendar_input.daterangepicker('clearRange');
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
              _this.deactiveFilterBackground(this);
          }else{
              months =_.map(months, Number);
          }
          _this.filters.trigger('months_change', months);
      });
      // Create calendar anchor
      var calendar_input = $('<input>', {'id': 'calendar_input'})
          .appendTo(div_time);
      options = {
        datepickerOptions : {
          numberOfMonths : 1,
          //dayNames: [ "Diumenge", "Dilluns", "Dimarts", "Dimecres", "Dijous", "Divendres", "Dissabte" ],
          firstDay: 1,
          //monthNamesShort: [ "Gen", "Feb", "Mar", "Abr", "Maig", "Juny", "Jul", "Ago", "Set", "Oct", "Nov", "Des" ],
          maxDate: null,
          minDate:new Date(2014,5,1)
        },
        applyOnMenuSelect: false,
        altFormat: "yyyy-mm-dd",
        dateFormat: "dd/mm/yy"
      };
      trans.on('i18n_lang_changed', function(){
        month_names = [];
        months.forEach(function(month, idx) {
          if (month[0]!='all') month_names.push(t(month[1]));
        });
        presets = [];
        MOSQUITO.config.calendar_presets.forEach(function(obj, idx) {
          var newobj = _.extend({}, obj);
          newobj.text = t(newobj.text);
          presets.push(newobj);
        });
        lang_options = {
          datepickerOptions : {
            dayNamesMin: [
              t('general.shortday.sunday'),
              t('general.shortday.monday'),
              t('general.shortday.tuesday'),
              t('general.shortday.wednesday'),
              t('general.shortday.thursday'),
              t('general.shortday.friday'),
              t('general.shortday.saturday')
            ],
            monthNames: month_names,
            nextText: t('general.next'),
            prevText: t('general.previous')
          },
          presetRanges: presets,
          initialText: t('group.filters.time.custom_daterange'),
          applyButtonText: t('group.filters.time.apply'),
          clearButtonText: t('group.filters.time.clear'),
          cancelButtonText: t('group.filters.time.cancel'),
        };
        calendar_input.daterangepicker(lang_options);
      });
      calendar_input.daterangepicker(options);
      calendar_input.prevRange = null;
      calendar_input.on('change', function() {
        var range = calendar_input.daterangepicker('getRange');
        if (range !== null) {
          $('.comiseo-daterangepicker-triggerbutton').addClass('selected-filter-button');
          if (select_months.val().indexOf('all') === -1)
              select_months.val('all').trigger('change');
          if (select_years.val().indexOf('all') === -1)
              select_years.val('all').trigger('change');
        } else {
          $('.comiseo-daterangepicker-triggerbutton').removeClass('selected-filter-button');
        }
        if (calendar_input.prevRange !== range)
            _this.filters.trigger('daterange_change', range);
        calendar_input.prevRange = range;
      });
      //
      if(this.filters.daterange && typeof this.filters.daterange !== 'undefined'){
          calendar_input.daterangepicker('setRange', this.filters.daterange);
      }
    },

    addHashtagFilterTo: function(section) {
      var _this = this;

      var div_hashtag = this.newFilterGroup({
        'id': 'hashtag_filters',
        'title': 'group.filters.hashtag'
      });
      if (div_hashtag) div_hashtag.appendTo(section);

      div_hashtag.html('<form class="hashtag_form" onsubmit="return:false">'+
              '<div style="display:flex;">' +
              '    <input id="hashtag_search_text" type="text" placeholder="#hashtag" value="">' +
              '    <button id="hashtag_button_search" type="submit"><i class="fa fa-search"></i></button>' +
              '    <button id="hashtag_button_trash" type="submit"><i class="fa fa-trash"></i></button>' +
              '</div></form>');

      if (this.filters.hashtag && this.filters.hashtag!='N'){
        $('#hashtag_search_text').val(this.filters.hashtag);
        _this.activeFilterBackground($('#hashtag_search_text'));
      }

      $('#hashtag_button_search').click(function(){
          _this.filters.trigger('hashtag_change', $('#hashtag_search_text').val());
          if ($('#hashtag_search_text').val()==''){
            $('#hashtag_search_text').removeClass('active');
          }
          else{
            $('#hashtag_search_text').addClass('active');
          }
          return false;
      });
      $('#hashtag_button_trash').click(function(){
          $('#hashtag_search_text').val('')
          $('#hashtag_search_text').removeClass('active');
          _this.filters.trigger('hashtag_change', '');
          return false;
      });

      $('#hashtag_search_text').change(function(){
          if ($(this).val()===''){
            _this.deactiveFilterBackground($(this));
            _this.filters.trigger('hashtag_change', $('#hashtag_search_text').val());
          }
          else{
            _this.activeFilterBackground($(this));
          }
      });
    },

    addNotificationFiltersTo: function(section) {
      //ONLY MANAGERS AND SUPERMOSQUITO
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

      if (isManager || isSuperUser) {
          var div_notif = this.newFilterGroup({
            'id': 'notif_filters',
            'title': 'group.filters.notifications'
          });
          if (div_notif) div_notif.appendTo(section);

          var select_notifications = $('<select>')
              .attr('class', 'notif_filter')
              .attr('id', 'select_notifications')
              .appendTo(div_notif);

          var notif_filter_all = $('<option>', {
                  "value": "all",
                  "i18n": "all_notifications",
                  "text": window.t().translate('es','all_notifications'),
                  "selected": "selected"
                }).appendTo(select_notifications);

          var notif_filter_mine = $('<option>', {"value": "withmine", "i18n": "with_my_notifications"})
              .appendTo(select_notifications);

          var notif_filter_notmine = $('<option>', {"value": "withoutmine", "i18n": "without_my_notifications"})
              .appendTo(select_notifications);

          select_notifications.on('change', function(){
            $('.notif_type_filter').val(['N']);
            $('.notif_type_filter').data('pre', ['N']);

            select_notifications.selectpicker('refresh');

            switch ($(this).val()) {
              case 'all':
                _this.filters.trigger('notif_change', false);
                _this.filters.trigger('notif_type_change', ['N']);
                _this.deactiveFilterBackground(this);
              break;
              case 'withmine':
                _this.filters.trigger('notif_change', 1);
                MOSQUITO.app.mapView.filters.notif_type = '0';
                _this.activeFilterBackground(this);
              break;
              case 'withoutmine':
                _this.filters.trigger('notif_change', 0);
                _this.activeFilterBackground(this);
              break;
            }
            _this.deactiveFilterBackground($(this).parent().siblings('.bootstrap-select').find('select'));
            select_type_notifications.selectpicker('refresh');
          });
          // notification types
          $('<br>').appendTo(div_notif);

          var select_type_notifications = $('<select multiple>')
              .attr('class', 'selectpicker notif_type_filter')
              .attr('id', 'select_type_notifications')
              .appendTo(div_notif);

          // onchage trigger
          select_type_notifications.selectpicker('refresh');
          select_type_notifications.data('pre', ['N']);
          select_type_notifications.on('change', function(event){
            var pre = $(this).data('pre');
            var now = $(this).val();
            // hem fet clic a una nova opció
            if (now !== null && pre !== null && typeof now !== 'undefined' && typeof pre !== 'undefined' && pre.length < now.length) {
              pre.forEach(function(elem) {
                now.splice(now.indexOf(elem),1);
              });
            }
            // si hem fet clic a TODOS
            if (!now || (now.length === 1 && now[0] === 'N') || (now.length === 0)) {
              $(this).val(['N']);
              _this.deactiveFilterBackground(this);
            } else {
              if ($(this).val().indexOf('N') !== -1) {
                let options = $(this).val();
                options.splice(options.indexOf('N'),1);
                $(this).val(options);
                _this.activeFilterBackground(this);
              }
              $('.notif_filter').val('all');
            }

            $(this).data('pre', $(this).val());
            select_type_notifications.selectpicker('refresh');
            select_notifications.selectpicker('refresh');
            _this.filters.trigger('notif_type_change', $(this).val());

            //deactivate my notifs filter
            _this.deactiveFilterBackground($(this).parent().siblings('.bootstrap-select').find('select'));
          });

          $('div.bootstrap-select.notif_type_filter').on('click', function(e){
            var maxAllowedHeight = parseInt($('#notif_filters').offset().top);
            var divHeight = parseInt($('#notif_filters').height());
            $(this).find('ul.dropdown-menu.inner').css('max-height', (maxAllowedHeight - divHeight))
          });
          // populate the filter with values
          $.ajax({
            "url": MOSQUITO.config.URL_API + 'notifications/predefined/',
            "complete": function(result, status) {
              if (status == 'success') {
                $('<option>', {
                    'value': 'N',
                    'text': t('map.notification.type.filters.title'),
                    'i18n': 'map.notification.type.filters.title',
                    'selected': true
                  }).appendTo(select_type_notifications);

                result.responseJSON.notifications.forEach(function(type,b) {
                  var lng = (typeof MOSQUITO.lng == 'array')?MOSQUITO.lng[0]:MOSQUITO.lng;
                  //if there is translation, then add it as i18n attribute, else add label text
                  if ((type.content[lng].title) in trans[MOSQUITO.lng]){
                    var label = t(type.content[lng].title);
                    //Add label in proper lng, and add i18n for future lang changes
                    $('<option>', {
                        "value": type.id,
                        "i18n":type.content[lng].title,
                        "text":label,
                       }).appendTo(select_type_notifications);
                  }
                  else{
                    var label = type.username.charAt(0).toUpperCase()+type.username.slice(1)+' / '+type.content[lng].title;
                    $('<option>', {
                      'value': type.id,
                      'text': label
                    }).appendTo(select_type_notifications);
                  }
                });
                //refresh selectpicker
                select_type_notifications.selectpicker('refresh');
              } else {
                console.error("An error was found while trying to get the list of notification types");
              }

            }
          });
      }
    },

    addMunicipalitiesTokensLiteners: function (){
      $('#tokenfield').on('change', function(e){
          $('#municipalities-checkbox').prop('checked', false);
          if ($('#tokenfield').val()){
            var value = _this.getSelectedMunicipalitiesId();
          }
          else value = 'N';

          _this.filters.trigger('municipalities_change', value);
      });

      $('#tokenfield').on('tokenfield:createdtoken', function (e) {
          // Über-simplistic e-mail validation
          $(e.relatedTarget).attr('data-value',e.attrs.id)
          $(e.relatedTarget).find('.token-label').css('max-width', $(e.relatedTarget).parent().width() - 30);
      })

      $('#tokenfield').on('tokenfield:createtoken', function (event) {
        if (typeof event.attrs.id==='undefined'){
            event.preventDefault();
        }

        var existingTokens = $(this).tokenfield('getTokens');
        $.each(existingTokens, function(index, token) {
            if (token.label === event.attrs.label){
                event.preventDefault();
            }
        });
      });
    },

    addMunicipalityFiltersTo: function(section) {
      var _this = this;

      // Create time group
      var div_municipality = this.newFilterGroup({
        'id': 'municipality_group',
        'title': 'group.filters.municipalities'
      });

      if (div_municipality) {
        div_municipality.appendTo(section);
      }

      //Some registered users get input checkbox
      if (MOSQUITO.app.headerView.logged &&
          this.userCan('notification') ) {
        var input_user_municipalities = $('<input>')
            .attr('type', 'checkbox')
            .attr('id', 'municipalities-checkbox')
            .appendTo(div_municipality);

        var label_my_municipalities = $('<span>')
            .attr('i18n', 'label.user-municipalities')
            .appendTo(div_municipality);

        input_user_municipalities.on('change', function(e){
          _this.emptyMunicipalitiesSearch();
          _this.initMunicipalitiesSelect();

          if (this.checked){
            _this.filters.trigger('municipalities_change', '0');
          }
          else{
            _this.filters.trigger('municipalities_change', 'N');
          }
        })
      }

      // Create year select
      var select_municipalities = $('<input>')
          .attr('class', 'form-control')
          .attr('id', 'tokenfield')
          .appendTo(div_municipality);

      //Add events for municipalities tokenfield
      this.addMunicipalitiesTokensLiteners();

      if (this.filterMunicipalitisIsEmpty()){
        this.initMunicipalitiesSelect();
      }
      else{
        this.setMunicipalitiesInFilter();
      }

    },

    addFiltersInPanelLayers: function(){
        var _this = this;
        _.extend(this.filters, Backbone.Events);

        if (MOSQUITO.app.headerView.logged){
          var container = $('div#iduserdata');
        }
        else{
          var container = $('div#idmodels');
        }

        //Add filter accordion
        var toggleGrup = $('<div/>')
            .attr('data-toggle','collapse')
            .attr('data-target', '#div_filters')
            .attr('class','layer-group-trigger')
            .attr('aria-expanded',"false")
            .attr('id', 'idfilters')
        .insertBefore(container);

        var parentDiv = $('<div/>')
            .attr('class', 'layer-group list-group-item')
        .appendTo(toggleGrup);

        let question_mark = $('<a>', {
          'tabindex':'0',
          'role': 'button',
          'data-trigger': 'focus',
          'data-placement':'left',
          'i18n': 'filters.description|data-content',
          'data-container': 'body',
          'class':'fa fa-question question-mark-toc question-mark-filters',
          'id': 'question_mark_filters'
        })
        var questionDiv = $('<div>')
          .attr('id', 'question_mark_container')

        //after question mark
        $('<div/>')
           .attr('id', 'filters_accordion')
           .attr('i18n', 'group.filters')
           .attr('class','group-title')
       .appendTo(parentDiv)

       question_mark.appendTo(questionDiv)
       questionDiv.appendTo(parentDiv)

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

        var divGroup = $('<div>')
            .attr('id', 'div_filters')
            .attr('class', 'collapse') //+(!group.collapsed?'in':''))
        .insertBefore(container);

        //Start adding filters to filters accordion
        var filtersSection = $('<div>')
            .attr('id', 'map_filters')
            .attr('class', 'filters_group')
            .appendTo(divGroup);

        this.addTimeFiltersTo(filtersSection);

        this.addHashtagFilterTo(filtersSection);

        this.addNotificationFiltersTo(filtersSection);

        this.addMunicipalityFiltersTo(filtersSection)

        if (this.anyFilterChecked()){
          this.activateFilterAcordion();
        }

        trans.on('i18n_lang_changed', function(){
          setTimeout(function(){
              $('#select_years').selectpicker('refresh');
              $('#select_months').selectpicker('refresh');

              //reset municipalities select2
              _this.initMunicipalitiesSelect();

              _this.checkFiltersBackground();
              if (MOSQUITO.app.headerView.logged) {
                $('#select_notifications').selectpicker('refresh');
                $('#select_type_notifications').selectpicker('refresh');
                $('.epi-select').selectpicker('refresh');
              }
          }, 0);
        });
    },

    filterMunicipalitisIsEmpty: function(){
        return (this.filters.municipalities == 'N')
    },

    setMunicipalitiesInFilter: function(){
      if (MOSQUITO.app.headerView.logged){
        if (_this.filters.municipalities.toString()=='0'){
          $('#municipalities-checkbox').prop('checked','true');
          return true;
        }
      }

      _this = this;
      $.ajax({
          url:  MOSQUITO.config.URL_API + 'get/municipalities/id/',
          type: 'POST',
          //data: params,
          data: _this.filters.municipalities.toString(),
          contentType: "application/json; charset=utf-8",
          context: this,
          success: function(result) {
              //Load layer even if it wasn't loaded
              if (result.data.length){
                _this.initMunicipalitiesSelect();
                //Prevent loading date each time filter is changed
                this.setDataLoading(false)
                result.data.forEach(function(e){
                  e = {'label':e.label, 'value':e.label, 'id':e.id}
                  $('#tokenfield').tokenfield('createToken', e);
                })
                this.setDataLoading(true)
              }
          }
      });
    },

    emptyMunicipalitiesSearch: function(){
        $('div.token').remove();
    },

    initMunicipalitiesSelect: function(){
      $('#tokenfield').tokenfield({
          autocomplete: {
            position: {my: "left bottom", at: "left top", collision: "flip flip"},
            source: function (request, response) {
              if (request.term.length >= MOSQUITO.config.min_length_region_search ){
                    jQuery.get(MOSQUITO.config.URL_API +"municipalities/search/", {
                        query: request.term
                    }, function (data) {
                        // data = $.parseJSON(data);
                        var t = [];
                        $.each(data,function(k,v){
                          t[k] = {'label':v.label, 'value':v.label, 'id': v.id};
                        })
                        response(t);
                    });
              }
              setTimeout(function() {
                var width = $('.tokenfield').outerWidth();
                var offset = $('.tokenfield.form-control').offset();
                $('.ui-menu.ui-widget.ui-widget-content.ui-autocomplete.ui-front').css('width', width);
                $('.ui-menu.ui-widget.ui-widget-content.ui-autocomplete.ui-front').css('left',offset.left);
              }, 100);
            },

            delay: 100
          },
          showAutocompleteOnFocus: true
          })

      $('#map-ui').scroll(function() {
        $('.ui-menu.ui-widget.ui-widget-content.ui-autocomplete.ui-front').css('display','none');
      });
    },

    getSelectedMunicipalitiesId: function(){
      var ids = []
      $('.tokenfield div.token').each(function(a,b) {
        ids.push($(b).attr('data-value'));
      })
      return ids.toString();
    },

    checkFiltersBackground: function(){
      if ($('#select_years').val().toString()!=='all'){
        this.activeFilterBackground($('#select_years'));
      }
      if ($('#select_months').val().toString()!=='all'){
        this.activeFilterBackground($('#select_months'));
      }
    },

    activateFilterAcordion: function(){
      $('#idfilters').find('.layer-group.list-group-item').addClass('active');
    },

    deactivateFilterAcordion: function(){
      $('#idfilters').find('.layer-group.list-group-item').removeClass('active');
    },

    activeFilterBackground: function(Elm){
      if ($(Elm).is('select')){
        $(Elm).closest('.bootstrap-select').find('button').addClass('selected-filter-button');
      }
      else if ($(Elm).is('input')){
        $(Elm).addClass('active');
      }
    },

    deactiveFilterBackground: function(Elm){
      if ($(Elm).is('select')){
        $(Elm).closest('.bootstrap-select').find('button').removeClass('selected-filter-button');
      }
      else if ($(Elm).is('input')){
        $(Elm).removeClass('active');
      }
    },

    dateParamsToString: function (){
        var url=''
        if (this.filters.daterange && typeof this.filters.daterange !== 'undefined') {
          url += '/' + moment(this.filters.daterange.start).format('YYYY-MM-DD');
          url += '/' + moment(this.filters.daterange.end).format('YYYY-MM-DD');
        } else {
          if(this.filters.years.length === 0){
              url += '/all';
          }else{
              url += '/' + this.filters.years;
          }

          if(this.filters.months.length === 0){
              url += '/all';
          }else{
              url += '/' + this.filters.months.join(',');
          }
        }
        return url
    },

    anyFilterChecked: function() {
        return (
            this.filters.years.length ||
            this.filters.months.length ||
            (this.filters.hashtag!==undefined && this.filters.hashtag != 'N' && this.filters.hashtag != '') ||
            (this.filters.notif!==undefined && this.filters.notif!==false) ||
            (this.filters.notif_types!==undefined && this.filters.notif_types[0]!='N') ||
            (this.filters.municipalities!==undefined && this.filters.municipalities!='N' ) ||
            ('daterange' in this.filters && this.filters.daterange !== null &&
              this.filters.daterange !== false)
          );
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

        //add private class to info template
        if (MOSQUITO.app.headerView.logged){
          $('ul#legend-container').addClass('private')
        }

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
            var url = MOSQUITO.config.URL_API + 'observations/export.xls';
            //prepare params based on filters
            url += '?bounds=' + this._map.getBounds().toBBoxString();
            if (_this.filters.daterange) {
              url += '&date_start=' + moment(_this.filters.daterange.start).format('YYYY-MM-DD');
              url += '&date_end=' + moment(_this.filters.daterange.end).format('YYYY-MM-DD');
            } else {
              if(_this.filters.years.length > 0){
                  url += '&years=' + _this.filters.years.join(',');
              }

              if(_this.filters.months.length > 0){
                  url += '&months=' + _this.filters.months.join(',');
              }
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
            url += '&mynotifs='+(('notif' in _this.filters && _this.filters.notif!==false)?_this.filters.notif:'N');

            //Check for notif_types filter
            notif_types='N'
            if ('notif_types' in _this.filters){
              if (_this.filters.notif_types!==null && _this.filters.notif_types!==false){
                notif_types = _this.filters.notif_types;
              }
              else
                notif_types = 'N';
            }

            url += '&notif_types='+ notif_types;

            //Add hashtag if exists, N otherwise
            if ('hashtag' in _this.filters && _this.filters.hashtag.trim()!=''){
              hashtag = _this.filters.hashtag.replace('#','');
              if (hashtag=='') hashtag='N'
            }
            else hashtag = 'N';
            url += '&hashtag='+hashtag;

            //Add municipalities if exists, N otherwise
            if ('municipalities' in _this.filters && _this.filters.municipalities.length>0){
              municipalities = _this.filters.municipalities;
            }
            else {
              municipalities = 'N';
            }
            url += '&municipalities='+municipalities;

            window.location = url;
        });


        btn.addTo(this.map);
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

            var longBbox = _this.map.getBounds().toBBoxString().split(',');
            var shortBbox = longBbox.map(function(x) {
               return (parseFloat(x).toFixed(4));
            });
            url += shortBbox.toString();

            if (_this.filters.daterange && typeof _this.filters.daterange !== 'undefined') {
              url += '/' + moment(_this.filters.daterange.start).format('YYYY-MM-DD');
              url += '/' + moment(_this.filters.daterange.end).format('YYYY-MM-DD');
            } else {
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

            //Add hashtag if exists and !=''
            url += ('hashtag' in _this.filters)?((_this.filters.hashtag.length)?'/'+_this.filters.hashtag:'/N'):'/N';

            //Add municipalities if exists
            url += ('municipalities' in _this.filters)?((_this.filters.municipalities.length)?'/'+_this.filters.municipalities:'/N'):'/N';

            //Add filters if exists and !=false(all selected)
            url += (('notif' in _this.filters)&&(_this.filters.notif!==false))?'/'+_this.filters.notif:'/N';

            //Add notif type filters if exists and != null
            url += (('notif_types' in _this.filters)&&(_this.filters.notif_types!==null))?'/'+_this.filters.notif_types:'/N';
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
                style: 'control-button',
                build_url: function(){
                  var layers = [];
                  //Get layers set to look for active layers

                  if (MOSQUITO.app.headerView.logged) {
                      //Accordion objects has list-group-item class
                      layersDiv = $('.sidebar-control-layers #div_observations ul > li.list-group-item, .sidebar-control-layers #div_none ul > li.list-group-only-item');
                  }
                  else{
                      // layersDiv = $('.sidebar-control-layers #div_none ul > li.list-group-only-item');
                      layersDiv = $('.sidebar-control-layers #div_observations ul > li.list-group-item, .sidebar-control-layers #div_none ul > li.list-group-only-item');
                  }
                  layersDiv.each(function(i, el){

                    if($(el).hasClass('active')){
                        //Get position of selected layers
                        id = $(el).attr('id').replace('layer_','');
                        if (MOSQUITO.config.keyLayersExcludedFromSharingURL.indexOf(id)==-1)  {
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
                        }
                        // layers.push(i+'');
                    }
                  });

                  //$lng/$zoom/$lat/$lon/$layers/$year/$months
                  var url  = document.URL.replace(/#.*$/, '');

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

                  if (layers.length === 0) layers.push('N');
                  url += '/' + layers.join();

                  url += _this.dateParamsToString()

                  //hashtag
                  if(!'hashtag' in _this.filters || typeof _this.filters.hashtag === 'undefined' || _this.filters.hashtag === ''){
                      url += '/N';
                  }else{
                      url += '/' + _this.filters.hashtag;
                  }

                    //municipalities
                    if(!'municipalities' in _this.filters || _this.filters.municipalities.length == 0){
                        url += '/N';
                    }else{
                        url += '/' + _this.filters.municipalities.toString();
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
            if(_this.scope.selectedMarker !== undefined && _this.scope.selectedMarker !== null){
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
                    //if not found
                    _this.scope.selectedMarker = null;
                    if($(_this.report_panel).is(':visible')){
                        _this.controls.sidebar.closePane();
                    }
                }
            }
        });
    },

    addPanelEpidemiology: function() {
      var _this = this;
      this.epi_panel = $('<div>')
        .attr('class', 'sidebar-epi-report');

      this.controls.sidebar.addPane(this.epi_panel);

      this.epi_panel.on('show', function(){
          if(_this.scope.selectedMarker !== undefined && _this.scope.selectedMarker !== null){
              _this.markerSetSelected(_this.scope.selectedMarker);
          }
          else{
              //hide panel
          }
      });

      this.epi_panel.on('hide', function(){
          if(_this.scope.selectedMarker !== undefined && _this.scope.selectedMarker !== null){
              _this.markerUndoSelected(_this.scope.selectedMarker);
          }
      })
    },

    show_epidemiology_report: function(marker){
      //out if not logged
      if (!MOSQUITO.app.headerView.logged) return false;
      var dict = {
          "indefinit":"undefined",
          "probable": "likely",
          "sospitos": "suspected",
          "confirmat": "form.confirmed-not-specified",
          "confirmat_den": "form.confirmed-den",
          "confirmat_chk": "form.confirmed-chk",
          "confirmat_yf": "form.confirmed-yf",
          "confirmat_zk": "form.confirmed-zk",
          "confirmat_wnv": "form.confirmed-wnv",
          'no_cas': 'nocase'
      }
      var panel = this.epi_panel;
      var epi_report = _.clone(marker).target.properties;
      epi_report.icon_src = this.getEpidemiologyPatientStateIcon(epi_report)
      lowerValue = epi_report.patient_state.toLowerCase()
      lowerValue = accentsTidy(lowerValue)
      lowerValue = lowerValue.replace(' ','_')
      epi_report.patient_state_shown = 'epidemiology.'+dict[lowerValue];
      this.controls.sidebar.closePane();
      if(!('epidemiology-tpl-content' in this.templates)){
          this.templates[
            'epidemiology-tpl-content'
          ] = $('#epidemiology-tpl-content').html();
      }

      //Check date
      epi_report.date_type='undefined'
      if (epi_report.date_arribal!==null){
        epi_report.date_type='arribal'
      }else{
        if (epi_report.date_notification!==null){
          epi_report.date_type='notification'
        }
      }

      var arribalDate = new Date(epi_report.date_arribal);
      //If not is date then do date
      if (! (arribalDate instanceof Date && !isNaN(arribalDate.valueOf())) ){
        epi_report.date_arribal = arribalDate.getDate() +
                '-' + ( arribalDate.getMonth() + 1 ) +
                '-' + arribalDate.getFullYear();
      }

      var notificationDate = new Date(epi_report.date_notification);
      //If not is date then do date
      if (! (notificationDate instanceof Date && !isNaN(notificationDate.valueOf())) ){
        epi_report.date_notification = notificationDate.getDate() +
                '-' + ( notificationDate.getMonth() + 1 ) +
                '-' + notificationDate.getFullYear();
      }

      var symptomDate = new Date(epi_report.date_symptom);
      //If not is date then do date
      if (! (symptomDate instanceof Date && !isNaN(symptomDate.valueOf())) ){
        epi_report.date_symptom = symptomDate.getDate() +
                '-' + ( symptomDate.getMonth() + 1 ) +
                '-' + symptomDate.getFullYear();
      }

      var tpl = _.template(this.templates['epidemiology-tpl-content']);
      this.scope.selectedMarker = marker.target;

      panel.html('');
      a = new L.Control.SidebarButton();
      a.getCloseButton().appendTo(panel);
      panel.append(tpl(epi_report));
      window.t().translate($('html').attr('lang'), panel);
      this.controls.sidebar.togglePane(panel, $('<div>'));
      if (!MOSQUITO.app.mapView.isMobile()){
        this.moveMarkerIfNecessary(marker.target);
      }
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

        if (!MOSQUITO.app.headerView.logged)  {
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
        this.scope.selectedMarker = marker;
        this.report_panel.html('');
        a = new L.Control.SidebarButton();
        a.getCloseButton().appendTo(this.report_panel);
        this.report_panel.append(tpl(nreport));

        //New notification button if applies
        if (MOSQUITO.app.headerView.logged && nreport.notifiable ){
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
                MOSQUITO.app.mapView.controls.notification.updateResults(MOSQUITO.app.mapView.scope.notificationClientIds,[' ']);
                MOSQUITO.app.mapView.controls.notification.getPredefinedNotifications();
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
        if (!MOSQUITO.app.mapView.isMobile()){
          this.moveMarkerIfNecessary(marker);
        }

        $('#map-ui .close_button').on('click', function(){
            _this.controls.sidebar.closePane();
        });
    },

    moveMarkerIfNecessary: function(marker){
      //Check if dragging selected is required
      var x = _this.map.getSize().x ;
      var y = _this.map.getSize().y ;
      var xMarker = _this.map.latLngToContainerPoint(marker.getLatLng()).x

      var mapIconsWidth = parseInt($('.leaflet-control-zoom-out').css('width')) + 40 //20px padding;
      var barWidth = parseInt($('.sidebar-report').css('width')) + mapIconsWidth;

      //if marker underneath future popup panel, then movie it
      var ne = _this.map.containerPointToLatLng([x - (barWidth + mapIconsWidth), 0]) ;
      //if (ne.lng < marker.getLatLng().lng)

      //if marker underneath future popup panel, then movie it
      if ( (x - xMarker) < barWidth){
        var sw = _this.map.containerPointToLatLng([0 , y]) ;
        var newBB = L.latLngBounds(sw, ne);
        var curCenter = _this.map.getCenter();
        var newCenter = newBB.getCenter();
        var moveLng = marker.getLatLng().lng - newCenter.lng;

        _this.forceReloadView = false;
        _this.map.setView( [curCenter.lat, curCenter.lng + moveLng], _this.map.getZoom());
      }
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
          str +='<li class="stormdrain_legend">'+
          '<div class="tr t-top">' +
            '<div class="tcel t-top">' +
            '<svg width="25px" height="20px" xmlns="http://www.w3.org/2000/svg">' + svgContent +
            '</svg></div>';

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

            str+='<div class="tcel"><span class="st-legendcategory" i18n="'+field_txt+'"></span></div>';

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
    },

    putEpidemiologyLegend: function(){
      var palette = this.epidemiology_palette
      var images = []
      var subgroups={}
      //dict for grouping legend elements
      for (var name in palette.images){
          if ('subgroup' in palette.images[name]) {
            if ( ! (palette.images[name].subgroup in subgroups) ){
                var obj = {'name': name, 'image': palette.images[name].img}
                subgroups[palette.images[name].subgroup]=[obj]
                images.push({"name": palette.images[name].subgroup, "image": palette.images[name].img})
            }
            else{
                var obj = {'name': name, 'image': palette.images[name].img}
                subgroups[palette.images[name].subgroup].push(obj)
            }
          }
          else{
                images.push({"name": name, "image": palette.images[name].img})
          }
      }
      //check if all subgroups are present in images array
      for (var group in subgroups){
          if ( !(images.indexOf(group))) {
            images.push({"name": group.name, "image": group.image})
          }
      }
      //all images and legend names
      var dict = {
        "indefinit":"undefined",
        "probable": "likely",
        "sospitos": "suspected",
        "confirmat": "confirmed-not-specified",
        "confirmat_den": "confirmed-den",
        "confirmat_chk": "confirmed-chk",
        "confirmat_yf": "confirmed-yf",
        "confirmat_zk": "confirmed-zk",
        "confirmat_wnv": "confirmed-wnv",
        'no_cas': 'nocase'
      }

      var selected_states = $('select[name=epidemiology-state]').val()
      var innerHTML=''

      images.forEach(function(val, ind, arr){
          if (
              (selected_states.indexOf(dict[val.name])!==-1)
              || (selected_states.indexOf('all')!==-1)
              || (val.name in subgroups)
            ) {

                  innerHTML += '<li class="epidemiology_legend">'
                  //check for groups
                  if (val.name in subgroups){
                      innerHTML += '<span i18n="epidemiology.group-'+val.name+'">' + t('epidemiology.group-'+val.name) + '</span>'
                      innerHTML += '<span class="show-group-legend">-</span>'
                      innerHTML += '<div class="legend-group legend-group-'+val.name+'">'
                      innerHTML += '<ul>'

                      subgroups[val.name].forEach(function(val, ind, arr){
                        if (
                            (selected_states.indexOf(dict[val.name])!==-1)
                            ||
                            (selected_states.indexOf('all')!==-1)
                        ) {
                          innerHTML += '<li class="epidemiology_legend"><img src = "' + val.image + '">'
                          innerHTML += '<span i18n="epidemiology.'+val.name+'">' + t('epidemiology.'+dict[val.name]) + '</span></li>';
                        }
                      })

                      innerHTML += '</ul></div>'
                  }
                  else{
                    innerHTML +=' <img src = "' + val.image + '">'
                    innerHTML += '<span i18n="epidemiology.'+dict[val.name]+'">' + t('epidemiology.'+dict[val.name]) + '</span>'
                  }
                  innerHTML += '</li>'
            }
       })

       $('#epidemiolgy_legend').html(innerHTML)
       $('.show-group-legend').click(function(e){
         e.stopPropagation();
         $(e.target).siblings('div').toggleClass('hidden')
         if ($(e.target).html()=='-'){
            $(e.target).html('+')
         }else{
             $(e.target).html('-')
         }
       })
    },

    //Make ajax call and prepare input, select and call stormDrainStyleUI to show style UI.
    stormDrainSetup:function(){
      //Ajax call to get params

      url = MOSQUITO.config.URL_API + 'stormdrain/setup/';
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

    },

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
                if (val=='null') {
                  $('.stormdrain_operator').trigger('change');
                }
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
    },

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
              url:  MOSQUITO.config.URL_API + 'stormdrain/setup/',
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

      //When Value selected is null then check operator.
      $('.stormdrain_value').on('change',function(){
          relatedOperator = $(this).parent().siblings().find('.stormdrain_operator');
          relatedOperatorValue = relatedOperator.val();
          var value = $(this).val();
          if (value=='null' && ['<=','>='].indexOf(relatedOperatorValue)!=-1){
            relatedOperator.val('=');
          }
        });

        //When Operator selected is null then check value.
        $('.stormdrain_operator').on('change',function(){
            relatedValue = $(this).parent().siblings().find('.stormdrain_value');
            relatedValueValue = relatedValue.val();
            var operator = $(this).val();
            if (relatedValueValue=='null' && ['<=','>='].indexOf(operator)!=-1){
              $(this).val('=');
            }
          });

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
    },

    stormDrainResetFormUpload: function(){
      $('.btn-st-template').show();
      $('#stormDrainUpload').find('.selected-file-name').val('');
      $('#stormDrainUpload').find('#stormdrain-upload-file').val('');
      $('input[name=stormdrain-title').val('');
      $('.stormdrain-upload-step1').show();
      $('#stormDrainUpload').find('.st-upload-error').hide();
      $('#stormDrainUpload').find('.stormdrain-import-started').hide();
      $('#stormDrainUpload').find('.stormdrain-import-finished').hide();
      $('#stormDrainUpload').find('.progress-bar-wrapper').hide();
      $('#stormDrainUpload').find('.stormdrain-upload-submit').show();
      $('#stormDrainUpload').find('.button-file').show();
      $('#stormDrainUpload').find('.stormdrain-upload-submit').show();
      $('#stormDrainUpload').find('.progress-bar-info').css('width','0%');
    },

    epidemiologyResetFormUpload: function(){
      $('.epi-upload-error').hide();
      $('.epi-button-file').show();
      $('#epiFormUpload').find('.selected-file-name').val('');
      $('#epidemiology-upload-file').val('');
      $('.epidemiology-modal-content').show();
      $('#epiFormUpload').find('.st-upload-error').hide();
      $('#epiFormUpload').find('.stormdrain-import-started').hide();
      $('.epi-import-finished-btn').hide();
      $('.epi-progress-bar-wrapper').hide();
      $('#epiFormUpload').find('.epidemiology-upload-submit').show();
      $('#epiFormUpload').find('.button-file').show();
      $('#epiFormUpload').find('.upload-submit').show();
      $('#epiFormUpload').find('.progress-bar-info').css('width','0%');
    },

    /* EVENTS ON STORMDRAIN MODAL WINDOW */
    stormDrainUploadEvents: function(){
      //Get template button
      $('.btn-st-template').on('click', function(){
        var url = MOSQUITO.config.URL_API + 'stormdrain/data/template/';
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
              url: MOSQUITO.config.URL_API +'stormdrain/data/',
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
                              $('.stormdrain-upload-step1').hide();
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

    },

    stormDrainUploadSetup: function(){
      _this = this;
      //Reset form just in case it was opened before
      this.stormDrainResetFormUpload();
      if (! ('stormdrain_upload_events' in this)){
          url = MOSQUITO.config.URL_API + 'stormdrain/setup/';
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
    },

    epidemiologyHasEvents: function(){
        return ('epidemiology_upload_events' in this)
    },

    /* EVENTS ON EPIDEMIOLOGY MODAL WINDOW */
    epidemiologyUploadEvents: function(){
      _this = this
      //Events only added once
      if (this.epidemiologyHasEvents()) return;

      //Get template
      $('.btn-epi-template').on('click', function(){
        var url = MOSQUITO.config.URL_API + 'epi/data/template/';
        window.location = url;
      })

      //Customized input file button
      $('#epidemiology-upload-file').on('change', function(){
          $('.epi-upload-error').hide();
          //$('.epi-progress-bar-wrapper').hide();
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

      $('.btn-epi-setup-now').on('click', function(){
          //close upload modal
          $('#epidemiology_upload').modal('hide');
          //trigger modal setup
          $('.fa-cog.epidemiology').trigger('click');

      })

      $('.btn-epi-setup-later').on('click', function(){
          $('#epidemiology_upload').modal('hide');
          _this.addEpidemiologyLayer()
          $('#layer_P').addClass('active');
      })

      $('.epidemiology-upload-submit').click(function(e){
        //submit function
        function epidemiologyUploadSubmit(callback){
          var form = $('form#epiFormUpload')[0];
          var formData = new FormData(form);
          $('.epi-progress-bar-wrapper').show();

          $.ajax({
              type: "POST",
              enctype: 'multipart/form-data',
              url: MOSQUITO.config.URL_API +'epi/data/',
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
                          $(".epi-progress-bar").html(percent+ "%");
                          $(".epi-progress-bar").width(percent + "%");
                          if (evt.loaded == evt.total){
                              $('.epidemiology-import-started-msg').show();
                          }
                      }, false);
                  }
                  return xhr;
              },
              success: function(data) {
                //hide/show stuff
                $('.epi-upload-error').html('').hide();
                $('.epidemiology-import-started-msg').hide();
                $('.epi-progress-bar-wrapper').hide();
                $('.epi-import-finished-btn').hide();
                if (data.success){
                  $('.epidemiology-upload-submit').hide();
                  $('.epidemiology-modal-content').hide();
                  $('.epi-import-finished-btn').show();
                }
                else{
                  txt_error = '<p class="st-upload-error">'+t('epidemiology.upload-error') + ':</br>' + data.err.toUpperCase() + '</p>' ;
                  $('.epi-progress-bar-wrapper').hide();
                  $('.epi-upload-error').html(txt_error);
                  $('.epi-upload-error').show();
                }
              },

              error: function() {
                $('.epi-import-finished-btn').hide();
                $('.epidemiology-import-started-msg').hide();
                $('.epidemiology-import-finished').hide();
                $('#epiFormUpload').find('.epidemiology-upload-submit').hide();
                $('#epiFormUpload').find('.epi-progress-bar-wrapper').hide();
                $('.epi-upload-error').html('Error')
                $('.epi-upload-error').show();
              },
              data: formData,
              cache: false,
              contentType: false,
              processData: false
          }, 'json');
        }

        val = $('#epidemiology-upload-file').val();
        if (val.length){
          $('.epi-upload-error').hide();
          epidemiologyUploadSubmit()
        }
        else{
          $('.epi-upload-error').html(t('epidemiology.upload-required'));
          $('.epi-upload-error').show();
        }
      })

    },

    epidemiologyUploadSetup: function(){
      this.epidemiologyResetFormUpload();
      this.epidemiologyUploadEvents();
      this.epidemiology_upload_events = true;
      $('#epidemiology_upload').modal('show');
    },

    epidemiologyFormSetup: function(){
      $('.epi-select').selectpicker('refresh');
      $('#select_epi-state').data('pre', $('#select_epi-state').val());
      $('#epidemiology_form_setup').modal('show');
      $('select[name=epidemiology-date]').val(this.epidemiology_palette_date)
      $('select[name=epidemiology-palette]').val(this.epidemiology_palette.name)
    }
});
