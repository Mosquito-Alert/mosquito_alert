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
});