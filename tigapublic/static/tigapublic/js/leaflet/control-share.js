var MOSQUITO = (function (m) {

    var ControlShare = L.Control.CustomButton.extend({
        style: 'leaflet-control-share-btn',
        build_url: function(){
            if(!(this.options.build_url)){
                if (console && console.error) console.error('ERROR: no options.build_url function defined');
            }
            return this.options.build_url();
        }
        ,
        onAdd: function(){
            L.Control.CustomButton.prototype.onAdd.call(this);

            var container = $('#control-share .content');
            this.panel = container;

            container.html($('#content-control-share-tpl').html());

            this.share_input = container.find('.share_input');

            // var set_url = function(){
            //     var url = this.build_url();
            //     share_input.val(url).trigger('change');
            // };

            this._map.on(
                'zoomend movestart move moveend layerchange', this.set_url, this);

            trans.on('i18n_lang_changed', this.set_url, this);
            //set_url.call(this);
            this.set_url();

            this.share_input.on('focus', function(){
                $(this).select();
            });

            var social_butons = container.find('.social-butons');
            var share_input_val  = this.share_input.val();
            social_butons.jsSocials({
                shares: [{
                            share: 'twitter',
                            //via: '',
                            //hashtags: '',
                            url: share_input_val
                        },
                        {
                            label: 'Share',
                            share: 'facebook',
                            //via: '',
                            hashtags: '',
                            url: share_input_val
                        }
                    ],
                text: t('share.look_at')+' @MosquitoAlert #cienciaciudadana',
                showCount: false
            });

            this.share_input.on('change', function(){
                social_butons.jsSocials('shareOption', 'twitter', 'url', $(this).val());
                social_butons.jsSocials('shareOption', 'twitter', 'text', t('share.look_at'));
                social_butons.jsSocials('shareOption', 'facebook', 'url', $(this).val());
            });

            return this._container;
        },

        set_url: function(){
            var url = this.build_url();
            this.share_input.val(url).trigger('change');
        },

        _click: function (e) {
            L.DomEvent.stopPropagation(e);
            L.DomEvent.preventDefault(e);
            this.set_url();
            $('#control-share').modal('show');
        }

    });

    m.control = m.control || {};
    m.control.ControlShare = ControlShare;

    return m;



    var ControlShare = L.Control.SidebarButton.extend({
        options: {
            style: 'leaflet-control-share-btn',
            position: 'topleft',
            title: '',
            text: '',
            active: false
        },
        getContent: function(){
            var container = $('<div>')
              .attr('class', 'sidebar-control-share');
            container.html($('#content-control-share-tpl').html());
            return container;
        },

        onAdd: function(){
            L.Control.SidebarButton.prototype.onAdd.call(this);
            var share_input = $(this.pane).find('.share_input');
            var set_url = function(){

                var layers = [];
                $('.sidebar-control-layers ul li').each(function(i, el){
                    if($(el).hasClass('active')){
                        layers.push(i+'');
                    }
                });

                //$lng/$zoom/$lat/$lon/$layers/
                var url  = document.URL.replace(/#.*$/, '');
                if(url[url.length-1] !== '/'){
                    url += '/';
                }
                url += '#';
                url += '/' + document.documentElement.lang;
                url += '/' + this._map.getZoom();
                url += '/' + this._map.getCenter().lat;
                url += '/' + this._map.getCenter().lng;
                url += '/' + layers.join();

                share_input.val(url).trigger('change');
            };
            this._map.on('zoomend movestart move moveend layerchange', set_url, this);
            trans.on('i18n_lang_changed', set_url, this);
            set_url.call(this);

            $(this.pane).find('.share_input').on('focus', function(){
                $(this).select();
            });

            // $(this.pane).on('show', function(){
            //     console.debug('show');
            // });
            // $(this.pane).on('hide', function(){
            //     console.debug('hide');
            // });

            var social_butons = $(this.pane).find('.social-butons');
            social_butons.jsSocials({
                shares: [{
                            share: 'twitter',
                            //via: '',
                            //hashtags: '',
                            url: share_input.val()
                        },
                        {
                            label: 'Share',
                            share: 'facebook',
                            //via: '',
                            hashtags: '',
                            url: share_input.val()
                        }
                    ],
                text: 'TODO',
                showCount: false
            });

            share_input.on('change', function(){
                social_butons.jsSocials('shareOption', 'twitter', 'url', share_input.val());
                social_butons.jsSocials('shareOption', 'facebook', 'url', share_input.val());
            });

            return this._container;
        },

    });

    m.control = m.control || {};
    m.control.ControlShare = ControlShare;

    return m;

}(MOSQUITO || {}));
