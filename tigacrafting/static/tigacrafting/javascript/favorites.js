
var set_favorited = function(report_id){
    var elem = $('*[data-report-icon="' + report_id + '"]');
    elem.removeClass("unfav");
    elem.addClass("fav");
    elem.prop("title", "Remove from favorites...");
}

var set_unfavorited = function(report_id){
    if(pending == 'favorite'){
        location.reload();
    }else{
        var elem = $('*[data-report-icon="' + report_id + '"]');
        elem.removeClass("fav");
        elem.addClass("unfav");
        elem.prop("title", "Add to favorites...");
    }
}

$(document).ready(function() {

    var favorite = function(report_id, user_id){
        $.ajax({
            url: '/api/favorite/',
            data: {'user_id': user_id, 'report_id': report_id},
            type: 'POST',
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function( data, textStatus, jqXHR ) {
                if(jqXHR.status == 200){
                    set_favorited(report_id);
                }else if(jqXHR.status == 204){
                    set_unfavorited(report_id);
                }
                update_favorite_counter();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
    }

    var update_favorite_counter = function(){
        $.ajax({
            url: '/api/user_favorites/',
            data: {'user_id': user_id},
            type: 'GET',
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function( data, textStatus, jqXHR ) {
                var n = data.length;
                $('#n_favorites').text(n);
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
    }

    var update_ui = function(){
        $.ajax({
            url: '/api/user_favorites/',
            data: {'user_id': user_id},
            type: 'GET',
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function( data, textStatus, jqXHR ) {
                for(var i = 0; i < data.length; i++){
                    set_favorited(data[i]);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
    }

    $(".fav_link").on('click', function(event){
        var report_id = $(this).data('report');
        var report_span = $('*[data-report-icon="' + report_id + '"]');
        if( report_span.hasClass("fav") ){
            if(confirm("Are you sure you want to remove the report from favorites?")){
                favorite( report_id, user_id );
            }
        }else{
            favorite( report_id, user_id );
        }
    });

    update_ui();
});