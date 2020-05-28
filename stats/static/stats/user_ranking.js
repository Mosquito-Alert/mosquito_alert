var cached_data = {};

var detail_template = '<div class="panel panel-default">' +
    '<div class="panel panel-heading">' +
        '<div class="row">' +
            '<div class="col-xs-12 stats">' +
                '<div class="row">' +
                    '<div class="col-xs-2">Joined</div><div class="col-xs-2"><span class="badge badge-success">#joined#</span></div>' +
                '</div>' +
                '<div class="row">' +
                    '<div class="col-xs-2">Last active</div><div class="col-xs-2"><span class="badge badge-success">#active#</span></div>' +
                '</div>' +
            '</div>' +
        '</div>' +
    '</div>' +
    '<div class="panel panel-body">' +
        '<div class="row">' +
            '<div class="col-xs-12 summary">' +
            '<div class="row">' +
                '<div class="col-xs-2"><b>Overall</b></div><div class="col-xs-2"><span class="badge badge-success"><b>#title_overall#</b></span></div>' +
            '</div>' +
             '<div class="row">' +
                '<div class="col-xs-2">Adult</div><div class="col-xs-3"><span class="badge badge-success">#title_adult#</span></div>' +
                 '<div class="col-xs-2">Reports</div><div class="col-xs-2"><span class="badge badge-success">#n_adult#</span></div>' +
                 '<div class="col-xs-2"><span class="badge badge-success">#xp_adult# XP</span></div>' +
             '</div>' +
             '<div class="row">' +
                '<div class="col-xs-2">Bite</div><div class="col-xs-3"><span class="badge badge-success">#title_bite#</span></div>' +
                 '<div class="col-xs-2">Reports</div><div class="col-xs-2"><span class="badge badge-success">#n_bite#</span></div>' +
                 '<div class="col-xs-2"><span class="badge badge-success">#xp_bite# XP</span></div>' +
             '</div>' +
             '<div class="row">' +
                 '<div class="col-xs-2">Site</div><div class="col-xs-3"><span class="badge badge-success">#title_site#</span></div>' +
                 '<div class="col-xs-2">Reports</div><div class="col-xs-2"><span class="badge badge-success">#n_site#</span></div>' +
                 '<div class="col-xs-2"><span class="badge badge-success">#xp_site# XP</span></div>' +
             '</div>' +
             '<div class="row">' +
                 '<div class="col-xs-2 col-xs-offset-7">Other XP</div><div class="col-xs-2"><span class="badge badge-success">#xp_unrelated#</span></div>' +
             '</div>' +
            '</div>' +
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
        html = html.replace(/#title_adult#/g, data.score_detail.adult.class_label);
        html = html.replace(/#title_bite#/g, data.score_detail.bite.class_label);
        html = html.replace(/#title_site#/g, data.score_detail.site.class_label);
        html = html.replace(/#title_overall#/g, data.overall_class_label);
        html = html.replace(/#xp_adult#/g, data.score_detail.adult.score);
        html = html.replace(/#xp_bite#/g, data.score_detail.bite.score);
        html = html.replace(/#xp_site#/g, data.score_detail.site.score);
        if(data.unrelated_awards.score != null){
            html = html.replace(/#xp_unrelated#/g, data.unrelated_awards.score);
        }else{
            html = html.replace(/#xp_unrelated#/g, "0");
        }

        $('#detail_' + user_uuid).html(html);
        cached_data[user_uuid] = data;
    }

    var load_user_data = function(user_uuid){
        $('#progress_' + user_uuid).show();
        if( cached_data[user_uuid] == null ){
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
                    create_info_div(user_uuid, data);
                },
                error: function(jqXHR, textStatus, errorThrown){
                    console.log(jqXHR.responseJSON);
                }
            });
        }else{
            create_info_div(user_uuid, cached_data[user_uuid]);
        }
    }

} );