$(document).ready(function() {

    var country_id = '';
    var user_id = '';

    $( "#dialog-confirm" ).dialog({
      resizable: false,
      height: "auto",
      width: 400,
      modal: true,
      autoOpen: false,
      buttons: {
        "Yes": {
            text: "Yes",
            id: "progress_yes",
            click: function(){
                $('#loading_progress').show();
                get_reports();
            }
        },
        "Cancel":{
            text: "Cancel",
            id: "progress_cancel",
            click: function(){
                $( this ).dialog( "close" );
            }
        }
      }
    });

    var get_reports = function(){
        var url = '/api/crisis_report_assign/' + user_id + '/' + country_id + '/';
        $("#progress_yes").prop("disabled",true);
        $("#progress_cancel").prop("disabled",true)
        $.ajax({
            url: url,
            type: "POST",
            headers: { "X-CSRFToken": csrf_token },
            success: function( data, textStatus, jqXHR ) {
                $('#loading_progress').html("<p>Done retrieving reports! Reloading...");
                window.location.href = '/experts';
            },
            error: function(jqXHR, textStatus, errorThrown){
                $("#progress_yes").prop("disabled",false);
                $("#progress_cancel").prop("disabled",false)
                $('#loading_progress').hide();
                alert("There has been an error and it's been impossible to assign reports. Please try again later.");
            }
        });
    }

    $('#grab_last_link').click(function(){
        country_id = $(this).data("country-last-id");
        user_id = $(this).data("user-id");
        var country_name = $(this).data("country-last-name");
        var n_reports = $(this).data("country-n");
        //console.log(country_id);
        var message = "You are about to grab reports from <b>" + country_name + "</b> which currently has <b>" + n_reports + "</b> reports available. Proceed?";
	    $('#dialog_message').html(message);
        $( "#dialog-confirm" ).dialog('open');
    });
});