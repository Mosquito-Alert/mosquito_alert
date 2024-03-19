$(document).ready(function () {
    var get_n_alerts = function(){
        $('#status_spinner').show();
        $.ajax({
            url: '/api/n_alerts/',
            type: "GET",
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            },
            success: function(data) {
                $('#status_spinner').hide();
                $('#n_alerts').text(data.n);
            },
            error: function(jqXHR, textStatus, errorThrown){
                $('#status_spinner').hide();
            }
        });
    }

    get_n_alerts();
});