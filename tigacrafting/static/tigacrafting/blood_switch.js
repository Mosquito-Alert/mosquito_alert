/* convenience function, sets status to female and adjusts ui accordingly */
var set_default_female = function( photo_id ) {
    var def = $.Deferred();
    $.ajax({
        url: '/api/photo_blood/',
        data: {'photo_id': photo_id, 'status': 'female'},
        type: 'POST',
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                var csrftoken = getCookie('csrftoken');
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
        success: function( data, textStatus, jqXHR ) {
            $('input:radio[name=fblood_' + photo_id + '][value=' + photo_id + '_female]').attr('checked',true);
            def.resolve();
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(textStatus);
            def.reject();
        }
    });
    return def.promise();
}

var reset_all_picture_status_for_report = function(report_id){
    var def = $.Deferred();
    $.ajax({
        url: '/api/photo_blood_reset/',
        data: {'report_id': report_id},
        type: 'POST',
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                var csrftoken = getCookie('csrftoken');
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
        success: function( data, textStatus, jqXHR ) {
            clear_all_report_radios(report_id);
            def.resolve();
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(textStatus);
            def.reject();
        }
    });
    return def.promise();
}

var clear_all_report_radios = function(report_id){
    $("[id^='blood_status_" + report_id + "_'] :input").attr('checked', false);
}

var show_blood_control = function(report_id, photo_id){
    $('#blood_status_' + report_id + '_' + photo_id).show();
}

$(document).ready(function() {

    var write_picture_status = function( photo_id, status ){
        $.ajax({
            url: '/api/photo_blood/',
            data: {'photo_id': photo_id, 'status': status},
            type: 'POST',
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function( data, textStatus, jqXHR ) {
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
    }

    $("input[type='radio'][name^='fblood_']").click(function() {
        var value = $(this).val();
        var photo_id = value.split("_")[0];
        var status = value.split("_")[1];
        write_picture_status(photo_id, status)
    });

    var show_control_by_species = function(annotation_id){
        var val = $('#category_' + annotation_id).val();
        if(val == '4' || val == '5' || val == '6' || val == '7' || val == '10'){
            return true;
        }else{
            return false;
        }
    }

    $("input:radio[name^='photo_to_display_report_']").click( function(){
        /* TODO - uncomment this when activating blood + female */
        var div_id = $(this).parent().attr('id');
        var report_id = div_id.split('_')[6];
        var ano_id = $(this).parent().data('ano-id')
        var show = show_control_by_species(ano_id);
        hide_blood_controls_for_report(report_id);
        var id_photo = $(this).attr('id');
        if(show){
            $('#blood_status_' + report_id + '_' + id_photo).show();
        }
        /*var radio_buttons = $(this).parent().children();
        if(show){
            radio_buttons.each(function(e){
                var input_id = $(this).attr('id');
                $('#blood_status_' + report_id + '_' + input_id).show();
            });
        }*/
        reset_all_picture_status_for_report(report_id).then(
            function(){
                set_default_female(id_photo);
            }
        );
    });

    var hide_blood_controls_for_report = function(report_id){
        $("[id^='blood_status_" + report_id + "_']").hide();
    }

    var hide_all_blood_controls = function(){
        $('[id^=blood_status_]').each(function(e){
            $(this).hide();
        });
    }

    var init = function(){
        hide_all_blood_controls();
        $("[id^='div_for_photo_to_display_report_'] :input").each(function(e){
            var this_id = $(this).attr('id');
            var parent_id = $(this).parent().attr('id');
            var report_id = parent_id.split('_')[6];
            if( $('#' + this_id ).is(':checked') || $('#' + this_id ).data('best') == 'True' ){
                $('#blood_status_' + report_id + '_' + this_id).show();
            }
        });
    }

    init();
});