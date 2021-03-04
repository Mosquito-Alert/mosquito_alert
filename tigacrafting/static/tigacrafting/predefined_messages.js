$(document).ready(function() {
    $('#lang_select option[value=en]').prop('selected', true);
    $('#species_select option[value=all]').prop('selected', true);
    var boxes = ['nice_picture','yes_thorax_pattern','no_thorax_pattern','not_sure_photo','other_species','other_insect','conflict'];
    var set_messages = function(lang,species){
        for(var i = 0; i < boxes.length; i++){
            var key = boxes[i];
            var message;
            if (key == 'yes_thorax_pattern' || key == 'no_thorax_pattern'){
                message = macro_messages[species][key][lang];
            }else{
                message = macro_messages['all'][key][lang];
            }
            if (message == null){
                message = "Not translated for current language";
            }
            $('#' + key).html( message );
        }
    };
    $('#lang_select').change(function(){
        var lang = $(this).val();
        var sp = $('#species_select').val();
        set_messages( lang, sp );
    });
    $('#species_select').change(function(){
        var lang = $('#lang_select').val();
        var sp = $(this).val();
        set_messages( lang, sp );
    });
    set_messages('en','all');
});