var reset_all_picture_status_for_report = function(report_id){
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
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(textStatus);
        }
    });
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

    $("[id^='div_for_photo_to_display_report_']").click( function(){
        var div_id = $(this).attr('id');
        var report_id = div_id.split('_')[6];
        var ano_id = $(this).data('ano-id')
        var show = show_control_by_species(ano_id);
        hide_blood_controls_for_report(report_id);
        reset_all_picture_status_for_report(report_id);
        $(this).children().each(function(e){
            var input_id = $(this).attr('id');
            if(show){
                $('#blood_status_' + report_id + '_' + input_id).show();
            }
        });
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