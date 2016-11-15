var HeaderView = Backbone.View.extend({
    el: '#header-view',
    events: {
      'click button': 'login',
      'click a.logout-button': 'logout'
      //'click button.logout-button': 'logout'
    },

    initialize: function(){
        this.render();
        this.$el.find('.logout-button').hide();
        this.$el.find('.login-button').hide();
        trans.on('i18n_lang_changed', function(lng){
            this.$el.find('a[data-lang]').removeClass('active');
            this.$el.find('a[data-lang="' + lng + '"]').addClass('active');
        }, this);
    },

    render: function(){
        if(MOSQUITO.config.login_allowed === true){
            var _this = this;
            MOSQUITO.app.on('app_logged', function(e){
                if(e === true){
                    _this.$el.find('.login-button').hide();
                    _this.$el.find('.logout-button').show();
                }else{
                    _this.$el.find('.logout-button').hide();
                    _this.$el.find('.login-button').show();
                }
            });
            this.is_logged();
        }
        return this;
    },

    is_logged: function(){

        $.ajax({
            type: 'GET',
            url:  MOSQUITO.config.URL_PUBLIC + 'ajax_is_logged/',
            success: function(response){
                MOSQUITO.app.trigger('app_logged', response.success);
            }
        });
    },

    login: function(){
        $.ajax({
            type: 'POST',
            url:  MOSQUITO.config.URL_PUBLIC + 'ajax_login/',
            data: {
                username: this.$el.find('#login_username').val(),
                password:  this.$el.find('#login_password').val()
            },
            success: function(response){
                MOSQUITO.app.trigger('app_logged', response.success);
            }
        });

    },
    logout: function(){
        var _this = this;
        //MOSQUITO.app.trigger('app_logged', false);
        $.ajax({
            url:  MOSQUITO.config.URL_PUBLIC + 'ajax_logout/',
            success: function(){
                _this.is_logged();
                MOSQUITO.app.trigger('app_logged', false);
            }
        });
    }
});
