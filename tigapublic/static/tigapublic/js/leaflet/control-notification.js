var MOSQUITO = (function (m) {

    var ControlNotification = L.Control.SidebarButton.extend({

        options: {
            style: 'leaflet-control-notification-btn',
            position: 'topleft',
            title: 'leaflet-control-notification-btn',
            text: 'Da',
            active: false
        },
        drawHandler: {},

        initialize: function(options) {
          L.Util.setOptions(this, options);
        },

        getContent: function(){
            var container = $('<div>').attr(
              'class', 'sidebar-control sidebar-control-notification'
            );
            var closeButton = this.getCloseButton().appendTo(container);
            container.append($('#content-control-notification-tpl').html());
            this.setup();
            if (MOSQUITO.app.headerView.logged && MOSQUITO.app.user.groups.indexOf('supermosquito') != -1) {
              $('#notification_form .warning').css('display','none');
            }
            return container;
        },

        "setup": function() {
            // if the layer does not exist, create it.
            if (!('capaNotificacion' in this)) {
              this.capaNotificacion = new L.FeatureGroup().addTo(this.map);
            }

            // set up the map control
            this.drawHandler = new L.Control.Draw({
                edit: {
                    featureGroup: this.capaNotificacion,
                    poly: {allowIntersection: false}
                },
                draw: {
                    polygon: {
                      allowIntersection: true,
                      showArea: true,
                      shapeOptions: {
                          stroke: true,
                          color: '#6f4702',
                          weight: 4,
                          opacity: 0.8,
                          fill: true,
                          fillColor: null, //same as color by default
                          fillOpacity: 0.4,
                          clickable: false,
                          editable:false
                      }
                    }
                }
            });

            this.map.addControl(this.drawHandler);

            trans.on('i18n_lang_changed', function(lng){
                L.drawLocal.draw.handlers.polygon.tooltip.cont = t('leaflet.draw.polygon.continue');
                L.drawLocal.draw.handlers.polygon.tooltip.end = t('leaflet.draw.polygon.end');
                L.drawLocal.draw.handlers.polygon.tooltip.start = t('leaflet.draw.polygon.start');
            }, this);

            // hide default UI
            $('.leaflet-draw.leaflet-control').css('display', 'none');

            // INTERACTIONS
            // when user clicks the submit button, do the submit
            $('.notification-submit').on('click', function(e) {
              this.submitForm($(e.target).closest('form').get(0));
            }.bind(this));

            // when finished drawing add the object to the layer
            this.map.on(L.Draw.Event.CREATED, function (event) {
                this.capaNotificacion.addLayer(event.layer);
            }.bind(this));
        },

        "updateResults": function(ids, usrs) {
            this.updateResultCounter(ids.length);
            this.updateUsersCounter(usrs.length);
        },

        "updateResultCounter": function(num) {
            $('#results_found').html(num);
        },

        "updateUsersCounter": function(num) {
            $('#users_found').html(num);
        },


        "enableFormAnchor": function(num) {
          $('#create_notification_btn').removeClass('disabled');
          $('#cancel_notification_btn').removeClass('disabled');
        },

        "disableFormAnchor": function() {
          $('#create_notification_btn').addClass('disabled');
          $('#cancel_notification_btn').addClass('disabled');
        },

        "getNotificationClientIds": function(){
            var filters = MOSQUITO.app.mapView.filters;
            // Iterate all poligons items and check user filters
            if ('notificationServerIds' in MOSQUITO.app.mapView.scope){

                MOSQUITO.app.mapView.scope.notificationClientIds = [];
                MOSQUITO.app.mapView.scope.number_of_users = [];
                MOSQUITO.app.mapView.scope.notificationServerIds.forEach(function(item){
                    MOSQUITO.app.mapView.scope.notificationClientIds.push(item.id);
                    //check if user is in number_of_users
                    if (MOSQUITO.app.mapView.scope.number_of_users.indexOf(item.user_id)==-1){
                      MOSQUITO.app.mapView.scope.number_of_users.push(item.user_id);
                    }
                });
                this.updateResults(
                      MOSQUITO.app.mapView.scope.notificationClientIds,
                      MOSQUITO.app.mapView.scope.number_of_users
                );
            }
        },

        "resetControl": function(){
            this.updateResultCounter(0);
            this.updateUsersCounter(0);
            this.capaNotificacion.clearLayers();
        },

        "startPolygonSelection": function() {
            MOSQUITO.app.mapView.scope.notifying = true;
            this.resetControl();

            // Hack
            // Emulate a click on the Leaflet-Draw control button
            var event = document.createEvent('Event');
            event.initEvent('click', true, true);
            var cb = document.getElementsByClassName('leaflet-draw-draw-polygon');
            !cb[0].dispatchEvent(event);

        },

        "finishPolygonSelection": function(e) {
          // load the geometry in the map
          var type = e.layerType,
              layer = e.layer;
          this.capaNotificacion.addLayer(layer);
          // get the polygon bounds
          polygon = e.layer.getLatLngs();
          filters = MOSQUITO.app.mapView.filters;

          MOSQUITO.app.mapView.scope.notificationSelection = [];
          polygon.forEach(function(obj) {
            MOSQUITO.app.mapView.scope.notificationSelection.push(obj.lng +' '+ obj.lat);
          });

          // Prepare url with filters
          var url = MOSQUITO.config.URL_API + 'notifications/intersect/';
          // layers
          url += filters.excluded_types.join(',')+'/';
          // time

          if (filters.daterange && typeof filters.daterange !== 'undefined') {
            // daterange
            url += moment(filters.daterange.start).format('YYYY-MM-DD') + '/'
            url += moment(filters.daterange.end).format('YYYY-MM-DD') + '/';
          } else {
            // years
            url += (filters.years.length)?filters.years.join(',') + '/':'all/';
            // months
            url += (filters.months.length)?filters.months.join(',') + '/':'all/';
          }

          // hashtag
          url += (MOSQUITO.app.mapView.filters.hashtag &&
                MOSQUITO.app.mapView.filters.hashtag !== '') ?
                    MOSQUITO.app.mapView.filters.hashtag + '/' : 'all/';
          //Municipalities
          var muni = MOSQUITO.app.mapView.getMunicipalitiesValue();
          //When no municipalities selected then pass 0 (user municipalities)
          url += (muni=='N')?'0/': muni + '/';
          // my notifications
          url += (filters.notif && filters.notif !== false)?filters.notif + '/':'N/';
          // notification typesstatus
          url += (MOSQUITO.app.mapView.filters.notif_types && (MOSQUITO.app.mapView.filters.notif_types.length > 1 || MOSQUITO.app.mapView.filters.notif_types[0] !== 'N'))?MOSQUITO.app.mapView.filters.notif_types.join(',') + '/':'N/';

          $.ajax({
              type: 'POST',
              context: this,
              url:  url,
              data: {'selection': MOSQUITO.app.mapView.scope.notificationSelection},
              cache: false,
              success: function(response){
                  if (response.success) {
                    MOSQUITO.app.mapView.scope.notificationServerIds = response.rows;
                    this.getNotificationClientIds();
                    this.getPredefinedNotifications();
                  }
              }

          });
          // set the working flag to false
          MOSQUITO.app.mapView.scope.notifying = false;
        },

        "getPredefinedNotifications": function(){
            $.ajax({
                type: 'POST',
                context: this,
                url:  MOSQUITO.config.URL_API + 'notifications/mypredefined/',
                cache: false,
                success: function(response){
                    if (response.success) {
                        MOSQUITO.app.mapView.scope.predefinedNotifications = response;
                        //REmove preset notifications, but first
                        $('#notification-presets').find('option').not(':first').remove();

                        //spanish version includes 3 languages
                        var defaultPresets = MOSQUITO.app.mapView.scope.predefinedNotifications['notifications'];
                        defaultPresets.forEach(function(item, index){
                          $('<option>')
                             .attr('name',index) //used to recover selected option text
                             .attr('value',item['id'])
                             .text(item['content']['es']['title'])
                             .appendTo($('#notification-presets'));
                        });
                        $('#notification-presets').selectpicker('refresh');
                        this.openForm();
                    } else {
                        alert(t('error.unknown')+': '+response.err);
                    }
                }
            });
        },

        "openForm": function(button) {
          if (!$(button).hasClass('disabled')) {
            //change form action
            $('#notification_file_input')
              .attr('action', MOSQUITO.config.URL_API + 'notifications/imageupload/');

            $('.form-group.notif-msg').addClass('hidden');
            $('#notification_form').modal('show');
            $('#preset_notification_id').val('0');
            setTimeout(function(){
                $('#notification-type').selectpicker('refresh');
                $('#notification-presets').selectpicker('refresh');
                $('#notification-notifier').val(t('map.notification.notifier') + ': ' + MOSQUITO.app.user.username);
                //Info about number of results
                var contentText =t('map.notification.notified') + ': ' + $('#results_found').html() + ' ' + t('map.results_found_text');
                //Plus info about number of users
                contentText += ' (' + $('#users_found').html() + ' ' + t('map.users_found_text')+')';
                $('#notification-notified').val(contentText);
                //If no notification show error on open form
                if (MOSQUITO.app.mapView.scope.notificationServerIds !== undefined && !MOSQUITO.app.mapView.scope.notificationServerIds.length){
                  $('#notif_observations_none').removeClass('hidden');
                }

            }, 0);

            //if tinymce was already init then reset contents
            if (tinymce.editors.length)
              this.resetForm();

            tinymce.init({
                mode : "specific_textareas",
                editor_selector : "notification_html",
                selector: '#notification_html',
                language: $('html').attr('lang'),
                plugins: 'link image advlist lists code table placeholder',
                image_advtab: true,
                file_browser_callback_types: 'image',
                file_browser_callback: function(field_name, url, type, win) {
                    if(type=='image') $('#notification_file_input input').click();
                },
                images_upload_url: MOSQUITO.config.URL_API + 'notifications/imageupload/',
                automatic_uploads: true,
                default_link_target: "_blank",
                link_assume_external_targets: true,
                link_title: false,
                statusbar: false,
                relative_urls : false,
                remove_script_host : false,
                convert_urls : true
            });
          }
        },

        "submitForm": function(form, args)  {
            $('.notif-msg').addClass('hidden');
            if ( !('notificationClientIds' in MOSQUITO.app.mapView.scope) ||
                  MOSQUITO.app.mapView.scope.notificationClientIds.length == 0 ) {
                $('#notif_observations_none').removeClass('hidden');
            }
            else if ( $('#notification-title').val()=='' ||
                      $('#notification-type').find("option:selected").index()==0 ||
                    tinyMCE.activeEditor.getContent()==''){
                $('#notif_all_field_requiered').removeClass('hidden');
            }
            else {
                data = {
                    "report_ids": MOSQUITO.app.mapView.scope.notificationClientIds,
                    "selection": MOSQUITO.app.mapView.scope.notificationSelection,
                    "type": $('#notification-type option:selected').attr('name'),
                    "expert_comment": $('#notification-title').val(),
                    "expert_html": tinyMCE.activeEditor.getContent(),
                    "preset_notification_id": $('#preset_notification_id').val()
                };
                //show sending message
                $('#sendig_notifications').removeClass('hidden');
                $.ajax({
                    type: 'POST',
                    context: this,
                    url:  MOSQUITO.config.URL_API + 'notifications/',
                    data: data,
                    cache: false,
                    success: function(response){
                        //hide sending message
                        $('#sendig_notifications').addClass('hidden');
                        if (response.success) {
                            $('.notif-msg').addClass('hidden');
                            $('#notif_saved').removeClass('hidden');
                            setTimeout(function(){
                                $('#notif_saved').addClass('hidden');
                                $('#notification_form').modal('hide');
                                this.resetControl();
                                form.reset();
                            }.bind(this), 1500);
                        } else {
                            $('#error_from_server').html(t('error.unknown') + ': ' + response.err);
                            $('#error_from_server').removeClass('hidden');
                            alert(t('error.unknown')+': '+response.err);
                        }
                    }
                });
            }
        },

        "setPredefined": function(obj) {
          selected = parseInt($(obj.options[obj.selectedIndex]).attr('name'));
          value = parseInt($(obj.options[obj.selectedIndex]).val());
          if (selected > -1) {
            var notifs = MOSQUITO.app.mapView.scope.predefinedNotifications.notifications;
            title = notifs[selected]['content']['es']['title'];
            body = notifs[selected]['content']['es']['body'];
            $('#preset_notification_id').val(value);
          } else {
            title = '';
            body = '';
            $('#preset_notification_id').val('0');
          }

          $('#notification-title').val(title);
          tinyMCE.activeEditor.setContent(body);
        }
        ,
        "resetForm":function(){
            tinymce.get('notification_html').setContent('');
            $('#notification-title').val('');
            $('#notification-type').val('');
        }


    });

    m.control = m.control || {};
    m.control.ControlNotification = ControlNotification;

    return m;

}(MOSQUITO || {}));
