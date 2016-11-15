var trans = trans || {};
_.extend(trans, Backbone.Events);
window.t = function(){
    if(arguments.length === 0){
        return {
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
                            translated = window.trans[lng][to_translate];
                            for(var l = 1; l < parts.length; l++){
                                $(el).attr(parts[l], translated);
                            }
                        }else{
                            translated = window.trans[lng][$(el).attr('i18n')];
                            $(el).html(translated);
                        }
                    }
                });
            },
            change: function(lng){
                $('html').attr('lang', lng);
                trans.trigger('i18n_lang_changed', lng);
                this.translate(lng, 'body');
            }
        };
    }else{
        var lng = $('html').attr('lang');
        //var userLang = navigator.language || navigator.userLanguage;
        var translated = window.trans[lng][arguments[0]] || arguments[0];
        //console.debug(translated);
        return translated;
    }
};
