var HeaderView = Backbone.View.extend({
    "logged": false,
    el: '#header-view',
    events: {
      'click button.login-submit': 'login',
      'click a.logout-button': 'logout',
      'click a.login-button': 'show_login_form'
      //'click button.logout-button': 'logout'
    },

    initialize: function(){
        this.render();
        //this.$el.find('.logout-button').hide();
        //this.$el.find('.login-button').hide();
        trans.on('i18n_lang_changed', function(lng){
            this.$el.find('a[data-lang]').removeClass('active');
            this.$el.find('a[data-lang="' + lng + '"]').addClass('active');
            if (this.logged) t().getLangFile(lng);
        }, this);
    },

    render: function(){
        if(MOSQUITO.config.login_allowed === true){
            var _this = this;
            MOSQUITO.app.on('app_logged', function(e){
                if(e === true && !MOSQUITO.config.embeded){
                    _this.logged = true;
                    $('body').addClass('logged');
                    _this.$el.find('.login-button').hide();
                    _this.$el.find('.logout-button').show();
                }else{
                    _this.$el.find('.logout-button').hide();
                    _this.$el.find('.login-button').show();
                }
            });
            this.is_logged();
        }
        var social_butons = $('html').find('.share-site-buttons');
        var url  = document.URL.replace(/#.*$/, '');
        social_butons.jsSocials({
            shares: [{
                        label: '',
                        share: 'twitter',
                        //via: '',
                        //hashtags: '',
                        url: url
                    },
                    {
                        label: '',
                        share: 'facebook',
                        //via: '',
                        hashtags: '',
                        url: url
                    }
                ],
            text: t('share.look_at')+' @MosquitoAlert #cienciaciudadana',
            showCount: false
        });
        return this;
    },

    "show_login_form": function() {
      //$('.collapse').removeClass('in');
      $('#control-login').modal('show');
      $('#control-login').on('shown.bs.modal', function() {
          $("#login_username").focus();
      });
    },

    is_logged: function(){
      var _this = this;
        $.ajax({
            type: 'GET',
            'async': true,
            url:  MOSQUITO.config.URL_API + 'ajax_is_logged/',
            success: function(response){
              MOSQUITO.config.availableVectorData = response.availableVectorData
              MOSQUITO.config.availableVirusData = response.availableVirusData
              MOSQUITO.config.availableBitingData = response.biting_models
              MOSQUITO.config.vector_municipalities ={}
              MOSQUITO.config.vector_grid ={}
              MOSQUITO.config.virus_municipalities ={}

              var dict = response.vector_models_by_municipality
              //do not include species with no data models (empty array)
              for (var specie in dict){
                if (dict[specie].length){
                  MOSQUITO.config.vector_municipalities[specie] = dict[specie]
                }
              }
              var dict = response.vector_models_by_grid
              for (var specie in dict){
                if (dict[specie].length){
                  MOSQUITO.config.vector_grid[specie] = dict[specie]
                }
              }

              var dict = response.virus_models_by_municipality
              for (var specie in dict){
                if (dict[specie].length){
                  MOSQUITO.config.virus_municipalities[specie] = dict[specie]
                }
              }

              MOSQUITO.app.user=response.data;
              MOSQUITO.app.trigger('app_logged', response.success);
            }
        }).fail(function(error) {
            console.log('no response from login')
            MOSQUITO.app.trigger('app_logged', false);
            MOSQUITO.config.predictionmodels_available = [];
            MOSQUITO.config.municipalities_models_available = [];
            MOSQUITO.config.virus_models_available = [];
        });
    },

    login: function(){
      if (this.$el.find('#login_username').length > 0 && this.$el.find('#login_password').length > 0 && this.$el.find('#login_username').val()!='' && this.$el.find('#login_password').val()!='') {
        var _this = this;
        $.ajax({
            type: 'POST',
            url:  MOSQUITO.config.URL_API + 'ajax_login/',
            data: {
                username: this.$el.find('#login_username').val(),
                password:  this.$el.find('#login_password').val()
            },
            success: function(response){
                if (response.success) {
                  var url = MOSQUITO.app.mapView.controls.share_btn.options.build_url();
                  document.location = url+'';
                  document.location.reload();
                } else {
                  alert(t('error.invalid_login'));
                }
            }
        });
      }
    },

    logout: function(){
        var _this = this;
        $.ajax({
            url:  MOSQUITO.config.URL_API + 'ajax_logout/',
            success: function(){
                MOSQUITO.app.mapView.controls.share_btn.options.build_url();
                _this.is_logged();
                MOSQUITO.app.trigger('app_logged', false);
            }
        });
    },

});
