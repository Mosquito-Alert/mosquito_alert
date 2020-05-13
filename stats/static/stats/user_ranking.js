

var detail_template = '<div class="row">' +
                             '<div class="col-md-6 stats">' +
                                 '<div class="row">' +
                                     '<div class="col-xs-6">Joined</div><div class="col-xs-6"><span class="badge badge-success">#joined#</span></div>' +
                                 '</div>' +
                                 '<div class="row">' +
                                     '<div class="col-xs-6">Last active</div><div class="col-xs-6"><span class="badge badge-success">#active#</span></div>' +
                                 '</div>' +
                             '</div>' +
                             '<div class="col-md-6 summary">' +
                                 '<div class="row">' +
                                     '<div class="col-xs-3">Adult reports</div><div class="col-xs-3 text-center"><span class="badge badge-success">#n_adult#</span></div>' +
                                     '<div class="col-xs-3">Adult XP</div><div class="col-xs-3 text-center"><span class="badge badge-success">#xp_adult#</span></div>' +
                                 '</div>' +
                                 '<div class="row">' +
                                     '<div class="col-xs-3">Bite reports</div><div class="col-xs-3 text-center"><span class="badge badge-success">#n_bite#</span></div>' +
                                     '<div class="col-xs-3">Bite XP</div><div class="col-xs-3 text-center"><span class="badge badge-success">#xp_bite#</span></div>' +
                                 '</div>' +
                                 '<div class="row">' +
                                     '<div class="col-xs-3">Site reports</div><div class="col-xs-3 text-center"><span class="badge badge-success">#n_site#</span></div>' +
                                     '<div class="col-xs-3">Site XP</div><div class="col-xs-3 text-center"><span class="badge badge-success">#xp_site#</span></div>' +
                                 '</div>' +
                             '</div>' +
                         '</div>';


$(document).ready(function() {
    //$('#datatable').DataTable();
    $('.clickable').click(function(event) {
        var id = $(this).attr('id');
        $('.info').attr( "style", "display:none;");
        $('#hidden_' + id ).fadeIn( "slow", function(){});
        load_user_data(id);
    });

    $('#scroll_to_me').click(function(event) {
        $([document.documentElement, document.body]).animate({
            scrollTop: $("#830424E9-3924-4D1C-849F-F5E62F4A14A8").offset().top
        }, 2000);
        $('#830424E9-3924-4D1C-849F-F5E62F4A14A8').addClass('pulse');
    });

    var create_info_div = function(user_uuid, data){
        $('#progress_' + user_uuid).hide();
        var html = detail_template.replace(/#joined#/g, data.joined_label);
        html = html.replace(/#active#/g, data.active_label);
        html = html.replace(/#n_adult#/g, data.score_detail.adult.score_items.length);
        html = html.replace(/#n_bite#/g, data.score_detail.bite.score_items.length);
        html = html.replace(/#n_site#/g, data.score_detail.site.score_items.length);
        html = html.replace(/#xp_adult#/g, data.score_detail.adult.score);
        html = html.replace(/#xp_bite#/g, data.score_detail.bite.score);
        html = html.replace(/#xp_site#/g, data.score_detail.site.score);
        $('#detail_' + user_uuid).html(html);
    }

    var load_user_data = function(user_uuid){
        $('#progress_' + user_uuid).show();
        $.ajax({
            url: '/api/stats/user_xp_data/?user_id=' + user_uuid,
            method: 'GET',
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    var csrftoken = getCookie('csrftoken');
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            },
            success: function( data, textStatus, jqXHR ) {
                console.log(data);
                create_info_div(user_uuid, data);
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(jqXHR.responseJSON);
            }
        });
    }

} );