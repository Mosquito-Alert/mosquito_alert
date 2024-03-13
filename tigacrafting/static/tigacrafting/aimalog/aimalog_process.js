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

    var load_status = function(alert_id){
        $.ajax({
            url: '/api/validation_status/' + alert_id + '/',
            type: "GET",
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            },
            success: function(data) {
                $('#status_spinner').hide();
                $('#status_label').text(data.status);
                if(data.n_reported!=null){
                    $('#reported_count').text(data.n_reported);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                $('#status_spinner').hide();
                $('#status_label').text("Error loading status: " + textStatus);
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
                //console.log(data);
            },
            error: function(jqXHR, textStatus, errorThrown){
                //console.log(textStatus);
            }
        });
    }

    var update_ui = function(){
        if(communication_status != '' && communication_status == '0'){
            //$('#new_comm').closest('.btn').button('toggle');
            $('input[name=communication_status][value=0]').attr('checked', true);
        }else if (communication_status != '' && communication_status == '1'){
            $('input[name=communication_status][value=1]').attr('checked', true);
            //$('#accepted_comm').closest('.btn').button('toggle');
        }else if (communication_status != '' && communication_status == '2'){
            $('input[name=communication_status][value=2]').attr('checked', true);
            //$('#sent_comm').closest('.btn').button('toggle');
        }else if (communication_status != '' && communication_status == '3'){
            $('input[name=communication_status][value=3]').attr('checked', true);
            //$('#rejected_comm').closest('.btn').button('toggle');
        }
    };

    /*
    $('input[type=radio][name=communication_status]').change( function(event) {
        event.preventDefault();
        event.stopPropagation();
        return false;

    });*/
    $('[name="communication_status"]:radio').click(function(event) {
        if(this.value==2){
            event.preventDefault();
        }
        var _current_status = this.value;
        set_communication_status(alert_id,_current_status);
    });

    $('#review').on('click', function(){
        var review_species = $('#review_species').val();
        var review_comment = $('#review_comment').val();
        review(alert_id, review_species, review_comment);
    });

    $('#comment').on('click',function(){
        var comments = $('#area_comments').val();
        review(alert_id, null, comments);
    });

    update_ui();
    load_status(alert_id);
    $("#send_email_modal").modal('show');

});