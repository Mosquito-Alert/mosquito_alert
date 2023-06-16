$( document ).ready(function() {

    var do_flip_report = function(version_uuid){
        $.ajax({
            url: '/api/flip_report/' + version_uuid + '/',
            type: 'POST',
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function( data, textStatus, jqXHR ) {
                console.log(data);
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
    };

    $(".flip_btn").click(function () {
        var version_uuid = $(this).data("id");
        do_flip_report(version_uuid);
    });
});