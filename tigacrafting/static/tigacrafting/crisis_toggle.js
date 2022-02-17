$(document).ready(function() {
    var set_crisis_on = function(){
        $('body').removeClass('bg-white');
        $('body').addClass('bg-danger');
        $('#crisis_status').removeClass('crisis-off');
        $('#crisis_status').addClass('crisis-on');
        $('#crisis_toggle').removeClass('btn-success');
        $('#crisis_toggle').addClass('btn-danger');
        $('#crisis_toggle span').text('ON');
    }
    var set_crisis_off = function(){
        $('body').removeClass('bg-danger');
        $('body').addClass('bg-white');
        $('#crisis_status').removeClass('crisis-on');
        $('#crisis_status').addClass('crisis-off');
        $('#crisis_toggle').removeClass('btn-danger');
        $('#crisis_toggle').addClass('btn-success');
        $('#crisis_toggle span').text('OFF');
    }

    var do_toggle = function(on_or_off){
        $('#crisis_toggle').prop("disabled",true);
        var url = '/api/toggle_crisis/';
        url = url + user + '/';
        $.ajax({
            url: url,
            type: "POST",
            headers: { "X-CSRFToken": csrf_token },
            success: function( data, textStatus, jqXHR ) {
                if( on_or_off == 1 ){
                    set_crisis_on();
                }else{
                    set_crisis_off();
                }
                $('#crisis_toggle').prop("disabled",false);
            },
            error: function(jqXHR, textStatus, errorThrown){
                alert("There has been an error and crisis mode has not been toggled. Please retry later");
                $('#crisis_toggle').prop("disabled",false);
            }
        });
    }

    $('#crisis_toggle').click(function(){
        if( $(this).text() == 'OFF' ){
            if( confirm("Do you really want to ACTIVATE crisis mode? This means that you will get reports from countries that are receiving a lot of activity right now.") ){
                do_toggle(1);
            }
        }else{
            if( confirm("Do you really want to DEACTIVATE crisis mode? This means that you will stop receiving reports from countries with a lot of activity, and will receive preferently reports from your area") ){
                do_toggle(0);
            }
        }
    });
});