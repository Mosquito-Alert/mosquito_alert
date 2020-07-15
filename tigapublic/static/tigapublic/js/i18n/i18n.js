var trans = trans || {};
_.extend(trans, Backbone.Events);
window.t = function(){
    if(arguments.length === 0){
        return {
            /*decode: function(text) {
                if (typeof text === 'undefined') return '';
                var APP_ROOT  = document.URL.replace(/#.*$/, '');
                return text.replace('{{APP_ROOT}}',APP_ROOT);
            },*/
            translate: function(lng, selector){
                $(selector).find('*[i18n]').each(function(i, el){
                    var translated,
                        to_translate = $(el).attr('i18n'),
                        type = el.nodeName;
                    if(type === 'IMAGE'){
                        //Alt
                    }else{
                        if(to_translate.indexOf('|') !==  -1){
                            var parts = to_translate.split('|');
                            to_translate = parts[0];
                            //translated = this.decode(window.trans[lng][to_translate]);
                            translated = window.trans[lng][to_translate];
                            for(var l = 1; l < parts.length; l++){
                                $(el).attr(parts[l], translated);
                            }
                        }else{
                            //translated = this.decode(window.trans[lng][$(el).attr('i18n')]);
                            translated = window.trans[lng][$(el).attr('i18n')];
                            $(el).html(translated);
                        }
                    }
                });
                // update select picker labels
                $('.selectpicker').selectpicker('refresh');
            },
            change: function(lng){
                $('html').attr('lang', lng);
                trans.trigger('i18n_lang_changed', lng);
                this.translate(lng, 'body');

                // do social buttons
                var social_butons = $('html').find('.share-site-buttons');
                social_butons.jsSocials('shareOption', 'twitter', 'text', t('share.look_at')+' @MosquitoAlert #cienciaciudadana');
                social_butons.jsSocials('shareOption', 'facebook', 'title', t('share.look_at')+' @MosquitoAlert #cienciaciudadana');
            },
            // load a new language file
            getLangFile: function(lng) {
              $.ajax({
                "url": "js/i18n/"+lng+"_logged.js",
                "complete": function(result, status) {
                  if (status=='success') {
                    eval (result.responseText);
                  }
                  window.t().translate(lng,'body');
                }
              });
            }
        };
    }else{
        var lng = $('html').attr('lang');
        var translated = window.trans[lng][arguments[0]] || arguments[0];
        return translated;
    }
};
