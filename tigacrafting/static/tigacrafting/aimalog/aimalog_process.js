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

    var status_update = function(expert_validation_category, status_in_location, loc_code, reported_n){
        $.ajax({
            url: '/api/status_update_info/',
            data: {
                'expert_validation_category': expert_validation_category,
                'status_in_location': status_in_location,
                'loc_code': loc_code,
                'reported_n': reported_n
            },
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
                $("#send_email_modal").modal('show');
                if(data.opcode=='nochange'){
                    $('#status_change_dialog').addClass('unchanged');
                    $('#status_change_dialog').text('unchanged');
                    $('#new_status').val('unchanged');
                }else{
                    $('#status_change_dialog').text(data.new_status);
                    $('#new_status').val(data.new_status);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
    }

    var load_status = function(alert_id){
        block_edit(true);
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
                $('#status_in_location').val(data.status);
                if(data.n_reported!=null){
                    $('#reported_count').text(data.n_reported);
                    $('#reported_n').val(data.n_reported);
                }
                block_edit(false);
            },
            error: function(jqXHR, textStatus, errorThrown){
                $('#status_spinner').hide();
                $('#status_label').text("Error loading status: " + textStatus);
                $('#reported_n').val('');
                $('#status_in_location').val('');
                block_edit(false);
            }
        });
    }

    var accept_and_communicate_alert = function(alert_id, new_status, expert_validation_category){
        $.ajax({
            url: '/api/accept_and_communicate_alert/',
            data: {'alert_id':alert_id, 'new_status':new_status, 'expert_validation_category': expert_validation_category},
            type: "POST",
            dataType: "json",
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            },
            success: function(data) {
                $("#send_email_modal").modal('hide');
                $('#sent_comm').prop('checked', true);
                toastr.success("Status correctly updated");
            },
            error: function(jqXHR, textStatus, errorThrown){
                $("#send_email_modal").modal('hide');
                toastr.error("Error changing status - " + errorThrown);
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
            $('input[name=communication_status][value=0]').attr('checked', true);
        }else if (communication_status != '' && communication_status == '1'){
            $('input[name=communication_status][value=1]').attr('checked', true);
        }else if (communication_status != '' && communication_status == '2'){
            $('input[name=communication_status][value=2]').attr('checked', true);
        }else if (communication_status != '' && communication_status == '3'){
            $('input[name=communication_status][value=3]').attr('checked', true);
        }
        if( report_in_progress == 1){
            block_edit(true);
            $('#noedit_alert').show();
        }
    };

    $('[name="communication_status"]:radio').click(function(event) {
        if(this.value==2){
            event.preventDefault();
            var expert_validation_category = $('#revised_category').val();
            var status_in_location = $('#status_in_location').val();
            var loc_code = $('#loc_code').val();
            var reported_n = $('#reported_n').val();
            status_update(expert_validation_category, status_in_location, loc_code, reported_n);
        }else{
            var _current_status = this.value;
            set_communication_status(alert_id,_current_status);
        }
    });

    $('#review').on('click', function(){
        var review_species = $('#review_species').val();
        var review_comment = $('#review_comment').val();
        review(alert_id, review_species, review_comment);
    });

    $('#confirm_review').on('click', function(){
        var expert_validation_category = $('#revised_category').val();
        var new_status = $('#new_status').val();
        accept_and_communicate_alert(alert_id, new_status, expert_validation_category);
    });

    $('#no_review').on('click', function(){
        $("#send_email_modal").modal('hide');
    });

    $('#comment').on('click',function(){
        var comments = $('#area_comments').val();
        review(alert_id, null, comments);
    });

    var block_edit = function(state){
        $('input[name=communication_status]').attr("disabled",state);
    };

    update_ui();
    load_status(alert_id);

});