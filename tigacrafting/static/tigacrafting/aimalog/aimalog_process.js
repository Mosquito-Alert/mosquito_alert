$(document).ready(function () {
    var review = function(alert_id, review_species, review_comments){
        $.ajax({
            url: '/api/review_alert/',
            data: {'alert_id':alert_id, 'review_species':review_species, 'review_comments':review_comments},
            type: "POST",
            dataType: "json",
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            },
            success: function(data) {
                console.log(data);
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
    }

    var set_communication_status = function(alert_id, communication_status){
        $.ajax({
            url: '/api/communication_status/',
            data: {'alert_id':alert_id, 'communication_status':communication_status},
            type: "POST",
            dataType: "json",
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            },
            success: function(data) {
                console.log(data);
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
    }

    var update_ui = function(){
        if(communication_status != '' && communication_status == '0'){
            $('#new_comm').closest('.btn').button('toggle');
        }else if (communication_status != '' && communication_status == '1'){
            $('#accepted_comm').closest('.btn').button('toggle');
        }else if (communication_status != '' && communication_status == '2'){
            $('#sent_comm').closest('.btn').button('toggle');
        }
    };

    $('input[type=radio][name=communication_status]').change(function() {
        var _current_status = this.value;
        set_communication_status(alert_id,_current_status);
    });

    $('#review').on('click', function(){
        var review_species = $('#review_species').val();
        var review_comment = $('#review_comment').val();
        review(alert_id, review_species, review_comment);
    });

    update_ui();

});