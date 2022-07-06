$(document).ready(function() {

    var clear_all = function(){
        var url = '/api/clear_blocked_all/';
        $.ajax({
            url: url,
            type: "DELETE",
            headers: { "X-CSRFToken": csrf_token },
            success: function( data, textStatus, jqXHR ) {
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown){
                toastr.error('Delete failed');
            }
        });
    }

    var clear_user = function(user){
        var url = '/api/clear_blocked/';
        url = url + user + '/';
        $.ajax({
            url: url,
            type: "DELETE",
            headers: { "X-CSRFToken": csrf_token },
            success: function( data, textStatus, jqXHR ) {
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown){
                toastr.error('Delete failed');
            }
        });
    }

    var clear_user_report = function(user, user_report){
        var url = '/api/clear_blocked_r/';
        url = url + user + '/';
        url = url + user_report + '/';
        $.ajax({
            url: url,
            type: "DELETE",
            headers: { "X-CSRFToken": csrf_token },
            success: function( data, textStatus, jqXHR ) {
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown){
                toastr.error('Delete failed');
            }
        });
    }

    $('.delete-user').click(function(e){
        var user_name = $(this).data('user');
        var response = confirm("Warning, you are about to clear all blocked reports for user " + user_name + " Proceed?")
        if( response == true){
            clear_user(user_name);
        }
    });

    $('.delete-report').click(function(e){
        var user_name = $(this).data('user');
        var report = $(this).data('report-id');
        var response = confirm("Warning, you are about to clear blocked report with uuid " + report + " for user " + user_name + " Proceed?")
        if( response == true){
            clear_user_report(user_name, report);
        }
    });

    $('.delete-all').click(function(e){
        var response = confirm("Warning, you are about to clear ALL blocked reports. Proceed?")
        if( response == true){
            clear_all();
        }
    });
});