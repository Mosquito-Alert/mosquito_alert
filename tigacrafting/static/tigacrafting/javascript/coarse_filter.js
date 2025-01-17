const ask_confirmation = false;

function make_site(report_id, type){
    hide_adult_buttons(report_id);
    $('#' + report_id).removeClass('adult');
    $('#' + report_id).removeClass('other');
    $('#' + report_id).addClass('site');
    $('#' + report_id).addClass(type);
    $('#' + report_id).data('type','site');
    $('#flip_' + report_id).data('type','site');
    $('#ia' + report_id).empty();
    $('#ia_label_' + report_id ).html('IA Value N/A');
    if(type=='other'){
        $('#label_' + report_id ).html('Breeding site - other');
    }else{
        $('#label_' + report_id ).html('Breeding site - storm drain');
    }
    $('#quick_upload_' + report_id).removeClass('hide_button');
}

function make_adult(report_id){
    show_adult_buttons(report_id);
    $('#' + report_id).removeClass('site');
    $('#' + report_id).removeClass('other');
    $('#' + report_id).removeClass('storm_drain');
    $('#' + report_id).addClass('adult');
    $('#' + report_id).data('type','adult');
    $('#flip_' + report_id).data('type','adult');
    create_graph( 'ia' + report_id );
    const ia_value = $('#ia' + report_id ).data('ia-value');
    const ia_f_value = Math.round(parseFloat(ia_value) * 100) / 100
    $('#ia_label_' + report_id ).html('IA Value ' + ia_f_value );
    $('#label_' + report_id ).html('Adult');
}

function set_report_visible_to(report_id, hide_value){
    const selector = `#visibility_${ report_id }`;
    const selector_hidden_button = `#hide_${ report_id }`;
    const selector_show_button = `#show_${ report_id }`;
    if(hide_value == 'true'){ //hidden
        $(selector).empty();
        $(selector).html('<span class="glyphicon glyphicon-eye-close" title="This report is hidden" style="color: white;"></span>');
        $(selector_hidden_button).addClass('hide_button');
        $(selector_show_button).removeClass('hide_button');
    }else{ //not
        $(selector).empty();
        $(selector).html('<span class="glyphicon glyphicon-eye-open" title="This report is visible" style="color: white;"></span>');
        $(selector_hidden_button).removeClass('hide_button');
        $(selector_show_button).addClass('hide_button');
    }
}

function show_adult_buttons(report_id){
    $(`#other_${ report_id }`).removeClass('hide_button');
    $(`#pculex_${ report_id }`).removeClass('hide_button');
    $(`#palbo_${ report_id }`).removeClass('hide_button');
    $(`#dalbo_${ report_id }`).removeClass('hide_button');
    $(`#ns_${ report_id }`).removeClass('hide_button');
    $(`#quick_upload_${ report_id }`).addClass('hide_button');
}

function hide_adult_buttons(report_id){
    $(`#other_${ report_id }`).addClass('hide_button');
    $(`#pculex_${ report_id }`).addClass('hide_button');
    $(`#palbo_${ report_id }`).addClass('hide_button');
    $(`#dalbo_${ report_id }`).addClass('hide_button');
    $(`#ns_${ report_id }`).addClass('hide_button');
    $(`#quick_upload_${ report_id }`).removeClass('hide_button');
}

$(document).ready(function() {

function type_shows_with_current_filter(type){
    const filtered_type = $('#type_select').val();
    if(filtered_type=='all'){
        return true;
    }else if(filtered_type==type){
            return true;
    }
    return false;
}

function report_shows_with_current_visibility(report_id){
    const is_visible = $('#visibility_' + report_id).hasClass('status_visible');
    const current_visibility = $('#visibility_select').val();
    if(current_visibility=='all'){
        return true;
    } else if ( current_visibility == 'visible' && is_visible ) {
        return true;
    } else if ( current_visibility == 'hidden' && !is_visible ) {
        return true;
    }
    return false;
}

function reset_filter(){
    $('#visibility_select').val('visible');
    $('#type_select').val('all');
    $('#country_select').val('all');
    $("#country_select_exclude").val("").change();
    $( "#slider" ).slider("value", 1.0);
    $( "#slider_value" ).html( "1.0" );
    $('#usernote_filter').val('');
}

function filter_to_ui(){
    const filter = ui_to_filter();
    const filter_json = JSON.parse(filter);
    $('#visibility_filter').html(filter_json.visibility_readable);
    $('#text_filter').html(filter_json.note);
    $('#rtype_filter').html(filter_json.report_type_readable);
    $('#country_filter').html(filter_json.country_readable);
    $('#country_filter_exclude').html(filter_json.country_exclude_readable);
    $('#ia_filter').html(filter_json.ia_threshold);
    $('#usernote_filter').html(decodeURI(filter_json.note));
}

function ui_to_filter(){
    const visibility = $('#visibility_select').val();
    const visibility_readable = $('#visibility_select option:selected').text();
    const report_type = $('#type_select').val();
    const report_type_readable = $('#type_select option:selected').text();
    const country = $('#country_select').val();
    const country_readable = $('#country_select option:selected').text();
    const country_exclude = $("#country_select_exclude").val();
    const country_exclude_readable = $("#country_select_exclude option:selected").text();
    const ia_threshold = $('#slider').slider('value');
    const note = escape($('#usernote_filter').val());
    return `
        {
            "visibility": "${visibility}",
            "visibility_readable": "${visibility_readable}",
            "report_type": "${report_type}",
            "report_type_readable": "${report_type_readable}",
            "country": "${country}",
            "country_exclude": "${country_exclude}",
            "country_readable": "${country_readable}",
            "ia_threshold": "${ia_threshold}",
            "note": "${note}"
        }
    `;
}

function resetchecks(){
    $('.n_choice').find('span').removeClass('glyphicon');
    $('.n_choice').find('span').removeClass('glyphicon-check');
}

function set_page_size(page_size){
    resetchecks();
    $('.n_choice').each( function(){
        if ( $(this).data('n_val') == page_size ){
            $(this).find('span').addClass('glyphicon');
            $(this).find('span').addClass('glyphicon-check');
            $('#n_per_page').val( $(this).data('n_val') );
        }
    });
}

function get_page_size(page_size){
    const size = $('#n_per_page').val();
    return size;
}

function create_ia_graph(){
    $('.ia_graph').each(function(){
        const id = $(this).attr('id');
        var type = $('#' + id).data('type');
        if(type=='adult'){
            try{
                create_graph( id );
            }catch(error){
                console.log(error);
            }
        }
    });
}

function update_pagination_data(pagination_data){
    set_current(pagination_data.current, pagination_data.count_pages, pagination_data.count);
    set_buttons(pagination_data);
    set_page_size(pagination_data.per_page);
    filter_to_ui();
}

function set_buttons(pagination_data){
    if(pagination_data.previous == null){
        $('#previous_page_button').hide();
    }else{
        $('#previous_page_button').show();
        $('#previous_page_button').data('offset', pagination_data.previous);
    }
    if(pagination_data.next == null){
        $('#next_page_button').hide();
    }else{
        $('#next_page_button').show();
        $('#next_page_button').data('offset', pagination_data.next);
    }
}

function set_current(current_page, n_pages, n_total){
    $('.current').html(`Page ${current_page} of ${n_pages}`);
    $('#n_pagination_reports').html(`${n_total}`);
    $('#n_query_reports').html(`${n_total}`);
}

function lockui(){
    $('#gear').show();
    $.blockUI();
}

function unlockui(){
    $('#gear').hide();
    $.unblockUI();
}

function load_previews(){
    var previews = [...document.querySelectorAll('.preview')].map((element, index) =>
        {
            return hoverPreview(element, {
                source : element.href
            });
        });
}

function set_visibility_icons(){
    $(".status_hidden").each(function (index, element) {
        $(this).html('<h4><span class="glyphicon glyphicon-eye-close" title="This report is hidden" style="color: white;"></span></h4>');
    });
    $(".status_visible").each(function (index, element) {
        $(this).html('<h4><span class="glyphicon glyphicon-eye-open" title="This report is visible" style="color: white;"></span></h4>');
    });
}

function remove_report(report_id){
    $('#' + report_id).remove();
    const n_reports = $('#n_query_reports').html();
    const n_reports_int = parseInt(n_reports);
    if(!isNaN(n_reports_int)){
        $('#n_query_reports').html( n_reports_int - 1 );
        $('#n_pagination_reports').html( n_reports_int - 1 );
    }
}

function hide_or_show_report(report_id, hide_value){
    $('#' + report_id).block({ message: 'Hiding or showing report' });
    $.ajax({
        url: '/api/hide_report/',
        data: { "report_id": report_id, "hide": hide_value },
        type: "PATCH",
        headers: { "X-CSRFToken": csrf_token },
        dataType: "json",
        success: function(data) {
            $('#' + report_id).unblock();
            const current_filter = ui_to_filter();
            const current_filter_json = JSON.parse(current_filter);
            if(current_filter_json.visibility=='all'){
                //redraw visibility icon
                set_report_visible_to(report_id, hide_value);
                if( hide_value == 'false' ){
                    if( $('#' + report_id).data('type') == 'adult' ){
                        show_adult_buttons(report_id);
                    }else{
                        hide_adult_buttons(report_id);
                    }
                }
            }else{
                remove_report(report_id);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            if( jqXHR.responseJSON.opcode == -1 ){
                alert("This report has been claimed by at least one expert, so it will be removed from the coarse filter.")
                remove_report(report_id);
            }
            $('#' + report_id).unblock();
        },
        cache: false
    });
}

function classify_picture(report_id, category_id, validation_value){
    $('#' + report_id).block({ message: 'Writing classification' });
    $.ajax({
        url: '/api/annotate_coarse/',
        data: { "report_id": report_id, "category_id": category_id, "validation_value": validation_value },
        type: "POST",
        headers: { "X-CSRFToken": csrf_token },
        dataType: "json",
        success: function(data) {
            $('#' + report_id).unblock();
            remove_report(report_id);
        },
        error: function(jqXHR, textStatus, errorThrown){
            if( jqXHR.responseJSON.opcode == -1 ){
                alert("This report has been claimed by at least one expert, so it will be removed from the coarse filter.")
                remove_report(report_id);
            }
            $('#' + report_id).unblock();
        },
        cache: false
    });
}

function quick_upload_report(report_id){
    $('#' + report_id).block({ message: 'Quick uploading report' });
    $.ajax({
        url: '/api/quick_upload_report/',
        data: { "report_id": report_id},
        type: "POST",
        headers: { "X-CSRFToken": csrf_token },
        dataType: "json",
        success: function(data) {
            $('#' + report_id).unblock();
            remove_report(report_id);
        },
        error: function(jqXHR, textStatus, errorThrown){
            if( jqXHR.responseJSON.opcode == -1 ){
                alert("This report has been claimed by at least one expert, so it will be removed from the coarse filter.")
                remove_report(report_id);
            }
            $('#' + report_id).unblock();
        },
        cache: false
    });
}

function flip_report(report_id, flip_to_type, flip_to_subtype){
    $('#' + report_id).block({ message: 'Flipping report' });
    $.ajax({
        url: '/api/flip_report/',
        data: { "report_id": report_id, "flip_to_type": flip_to_type, "flip_to_subtype": flip_to_subtype },
        type: "PATCH",
        headers: { "X-CSRFToken": csrf_token },
        dataType: "json",
        success: function(data) {
            $('#' + report_id).unblock();
            $('#modal_flip_to_site').modal('hide');
            const type = data.new_type;
            if( type_shows_with_current_filter(type) && report_shows_with_current_visibility(report_id) ){
                if(type=='adult'){
                    make_adult(report_id);
                }else if(type=='site'){
                    const subtype = data.new_subtype.startsWith('storm') ? "storm_drain" : "other";
                    make_site(report_id, subtype);
                }
            }else{
                remove_report(report_id);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            if( jqXHR.responseJSON.opcode == -1 ){
                alert("This report has been claimed by at least one expert, so it will be removed from the coarse filter.");
                remove_report(report_id);
            }else{
                alert(jqXHR.responseJSON.message);
                $('#modal_flip_to_site').modal('hide');
            }
            $('#' + report_id).unblock();
        },
        cache: false
    });
}

function load_data(limit=300, offset=1, q=''){
    lockui();
    $.ajax({
        url: `/api/coarse_filter_reports/?limit=${limit}&offset=${offset}&q=${q}`,
        type: "GET",
        dataType: "json",
        success: function(data) {
            unlockui();
            $('#photo_grid').empty();
            const root = $('#photo_grid');
            for(var i = 0; i < data.results.length; i++){
                const report = data.results[i];
                const single_report = single_report_template(report);
                root.append(single_report);
            }
            const pagination_data = {
                'per_page': data.per_page,
                'count_pages': data.count_pages,
                'current': data.current,
                'count': data.count,
                'next': data.next,
                'previous': data.previous,
            }
            update_pagination_data(pagination_data);
            create_ia_graph();
            init_maps();
            load_previews();
            set_visibility_icons();
        },
        error: function(jqXHR, textStatus, errorThrown){
            unlockui();
            console.log(errorThrown);
        },
        cache: false
    });
}

function single_picture_template(picture){
    return `
        <div class="picture_item">
            <a class="preview" href="${ picture.photo }" target="_blank">
                <img src="${ picture.small_url }">
                <!--<img src="${ picture.photo }" width="100" height="100">-->
            </a>
            <!--<img src="${ picture.photo }" width="100" height="100" >-->
        </div>
    `;
}

function pictures_template(pictures){
    const elements = pictures.reduce((acc, picture) => acc + single_picture_template(picture), "");
    return elements;
}

function single_report_template(report){
    const pictures = pictures_template(report.photos);
    const report_country_name = report.country == null ? 'No country' : report.country.name_engl;
    const site_cat = report.site_cat == 0 ? 'storm_drain' : 'other';
    const ia_value = report.prediction.photo_prediction.insect_confidence == null || report.type == 'site' ? 'N/A' : Math.round(report.prediction.photo_prediction.insect_confidence * 100) / 100;
    const adult_additional_button_class = report.type == 'site' || report.hide == true ? 'hide_button' : '';
    const hide_additional_button_class = report.hide == true ? 'hide_button' : '';
    const show_additional_button_class = report.hide == true ? '' : 'hide_button';
    const visibility_class = report.hide == true ? 'status_hidden' : 'status_visible';
    const user_notes = report.note == null || report.note == 'null' ? 'No notes' : report.note;
    const quick_upload_additional_button_class = report.type == 'adult' ? 'hide_button' : '';
    const formatted_lat = report.lat.toFixed(6);
    const formatted_lon = report.lon.toFixed(6);
    var report_type_label = '';
    if( report.type == 'adult' ){
        report_type_label = 'Adult';
    }else{
        report_type_label = report.site_cat == 0 ? 'Breeding site - storm drain' : 'Breeding site - other';
    }
    return `
        <div id="${ report.version_UUID }" data-type="${ report.type }" class="photo ${ report.type } ${ site_cat }">
            <div class="photo_internal_wrapper">
                <div class="header_internal_wrapper">
                    <div class="header_left">
                        <div class="header_country">
                            <a href="/single_simple/${ report.version_UUID }" target="_blank"><span class="label label-default"><span class="glyphicon glyphicon-link"> </span> ${ report_country_name }</span></a>
                        </div>
                        <div class="header_report_label_wrapper">
                            <div class="header_report_label"><span id="label_${report.version_UUID}" class="label label-default">${report_type_label}</span></div>
                        </div>
                        <div id="header_ia_${ report.version_UUID }" class="header_ia">
                            <div id="ia_label_${ report.version_UUID }">IA Value ${ ia_value }</div>
                            <div id="ia${ report.version_UUID }" data-ia-value="${ report.prediction.photo_prediction.insect_confidence }" data-type="${ report.type }" data-id="${ report.version_UUID }" class="ia_graph ${report.type}" style=""></div>
                        </div>
                        <div class="header_visibility">
                            <div id="visibility_${report.version_UUID}" class="${visibility_class}"></div>
                        </div>
                    </div>
                    <div class="header_right">
                        <div id="map_${ report.version_UUID }" class="maps map_${ report.version_UUID }" data-lat="${ report.lat }" data-lon="${ report.lon }">
                        </div>
                        <div class="lat_lon_wrapper">
                            <div>
                                <p><span class="label label-default">Lat: ${formatted_lat}</span></p>
                                <p><span class="label label-default">Lon: ${formatted_lon}</span></p>
                            </div>
                            <div class="lookup_button_wrapper">
                                <p><a class="btn btn-sm btn-primary" target="_blank" href="https://www.google.com/maps/place/${report.lat},${report.lon}">Lookup</a></p>
                            </div>
                        </div>
                    </div>
                </div>
                <hr class="hrnomargin">
                <div class="body_internal_wrapper">
                    <div class="label_wrapper">
                        <span class="label label-success">Id</span> ${ report.version_UUID }
                    </div>
                    <div class="label_wrapper">
                        <span class="label label-success">Date</span> ${ report.creation_time }
                    </div>
                    <div class="label_wrapper">
                        <span class="label label-success">User</span> ${ report.user_id }
                    </div>
                    <div class="label_wrapper">
                        <span class="label label-success">User Notes</span> ${ user_notes }
                    </div>
                </div>
                <hr class="hrnomargin">
                <div class="pictures_internal_grid_wrapper">
                    <div class="pictures_internal_grid">
                        ${ pictures }
                    </div>
                </div>
                <hr class="hrnomargin">
                <div class="buttons_internal_grid">
                    <button type="button" id="hide_${ report.version_UUID }" title="Hide report" data-report-id="${ report.version_UUID }" class="${ hide_additional_button_class } btn btn-primary foot_btn btn_hide_report">Hide</button>
                    <button type="button" id="show_${ report.version_UUID }" title="Show report" data-report-id="${ report.version_UUID }" class="${ show_additional_button_class } btn btn-primary foot_btn btn_show_report">Show</button>
                    <button type="button" id="other_${ report.version_UUID }" title="Other species" data-category="2" data-report-id="${ report.version_UUID }" class="${ adult_additional_button_class } btn btn-primary foot_btn btn_other">O.species</button>
                    <button type="button" id="pculex_${ report.version_UUID }" title="Probably culex" data-category="10" data-report-id="${ report.version_UUID }" class="${ adult_additional_button_class } btn btn-primary foot_btn btn_pculex">P.culex</button>
                    <button type="button" id="palbo_${ report.version_UUID }" title="Probably albopictus" data-category="4" data-report-id="${ report.version_UUID }" class="${ adult_additional_button_class } btn btn-primary foot_btn btn_palbo">P.albo.</button>
                    <button type="button" id="dalbo_${ report.version_UUID }" title="Definitely albopictus" data-category="4" data-report-id="${ report.version_UUID }" class="${ adult_additional_button_class } btn btn-primary foot_btn btn_dalbo">D.albo.</button>
                    <button type="button" id="ns_${ report.version_UUID }" title="Not sure" data-category="9" data-report-id="${ report.version_UUID }" class="${ adult_additional_button_class } btn btn-primary foot_btn btn_notsure">N.S.</button>
                    <button type="button" id="flip_${ report.version_UUID }" title="Change report type" data-type="${ report.type }" data-site-cat="${ site_cat }" data-report-id="${ report.version_UUID }" class="btn btn-danger foot_btn btn_notsure btn_flip">Flip</button>
                    <button type="button" id="quick_upload_${ report.version_UUID }" title="Set quick upload for site report" data-type="${ report.type }" data-report-id="${ report.version_UUID }" class="${ quick_upload_additional_button_class } btn btn-warning foot_btn btn_quick">Quick upload</button>
                </div>
            </div>
        </div>
    `;
}

$('#next_page_button').click( function(e){
    const offset = $(this).data('offset');
    const page_size = get_page_size();
    const filter = ui_to_filter();
    $('#filter_options').val(filter);
    load_data(page_size,offset,filter);
} );

$('#previous_page_button').click( function(e){
    const offset = $(this).data('offset');
    const page_size = get_page_size();
    const filter = ui_to_filter();
    $('#filter_options').val(filter);
    load_data(page_size,offset,filter);
} );

$('#reload_button').click( function(e){
    const offset = 1;
    const page_size = get_page_size();
    const filter = ui_to_filter();
    $('#filter_options').val(filter);
    load_data(page_size,offset,filter);
});

$('#page_button').click( function(e){
    const page = $('#page_input').val();
    const page_size = get_page_size();
    const filter = ui_to_filter();
    $('#filter_options').val(filter);
    if(page != ''){
        load_data(page_size,parseInt(page),filter);
    }
});

$('.n_choice').click( function(e){
    const child_span = $(this).find('span');
    if(!child_span.hasClass('glyphicon')){
        resetchecks();
        child_span.addClass('glyphicon');
        child_span.addClass('glyphicon-check');
    };
    $('#n_per_page').val( $(this).data('n_val') );
    const q = ui_to_filter();
    load_data( $(this).data('n_val'), 1, q);
});

$('#filters_submit_button').click( function(e){
    const offset = $(this).data('offset');
    const page_size = get_page_size();
    const filter = ui_to_filter();
    $('#filter_options').val(filter);
    $('#myModal').modal('hide');
    load_data(page_size,offset,filter);
});

$('#filters_clear').click( function(e){
    reset_filter();
    filter_to_ui();
    const page_size = get_page_size();
    const filter = ui_to_filter();
    $('#filter_options').val(filter);
    $('#myModal').modal('hide');
    load_data(page_size,1,filter);
});

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-primary.foot_btn.btn_hide_report', function(){
    const report_id = $(this).data("report-id");
    hide_or_show_report(report_id, "true");
});

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-primary.foot_btn.btn_show_report', function(){
    const report_id = $(this).data("report-id");
    hide_or_show_report(report_id, "false");
});

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-primary.foot_btn.btn_other', function(){
    const category_id = $(this).data("category");
    const report_id = $(this).data("report-id");
    if(ask_confirmation){
        if(confirm(`About to classify report with id ${report_id} as 'Other species'. Continue?`)==true){
            classify_picture(report_id, category_id, null);
        }
    }else{
        classify_picture(report_id, category_id, null);
    }
});

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-primary.foot_btn.btn_pculex', function(){
    const category_id = $(this).data("category");
    const report_id = $(this).data("report-id");
    if(ask_confirmation){
        if(confirm(`About to classify report with id ${report_id} as 'Probably Culex'. Continue?`)==true){
            classify_picture(report_id, category_id, 1);
        }
    }else{
        classify_picture(report_id, category_id, 1);
    }
});

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-primary.foot_btn.btn_palbo', function(){
    const category_id = $(this).data("category");
    const report_id = $(this).data("report-id");
    if(ask_confirmation){
        if(confirm(`About to classify report with id ${report_id} as 'Probably Albopictus'. Continue?`)==true){
            classify_picture(report_id, category_id, 1);
        }
    }else{
        classify_picture(report_id, category_id, 1);
    }
});

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-primary.foot_btn.btn_dalbo', function(){
    const category_id = $(this).data("category");
    const report_id = $(this).data("report-id");
    if(ask_confirmation){
        if(confirm(`About to classify report with id ${report_id} as 'Definitely Albopictus'. Continue?`)==true){
            classify_picture(report_id, category_id, 2);
        }
    }else{
        classify_picture(report_id, category_id, 2);
    }
});

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-primary.foot_btn.btn_notsure', function(){
    const category_id = $(this).data("category");
    const report_id = $(this).data("report-id");
    if(ask_confirmation){
        if(confirm(`About to classify report with id ${report_id} as 'Not sure'. Continue?`)==true){
            classify_picture(report_id, category_id, null);
        }
    }else{
        classify_picture(report_id, category_id, null);
    }
});

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-warning.foot_btn.btn_quick', function(){
    const report_id = $(this).data("report-id");
    if(ask_confirmation){
        if(confirm(`About to quick upload site report with id ${report_id}. Continue?`)==true){
            quick_upload_report(report_id);
        }
    }else{
        quick_upload_report(report_id);
    }
});

$("input[name='radio_report_type']").on('click', function(){
    const selected_value = $(this).val();
    $('#flip_to_type').val(selected_value);
    if(selected_value == 'adult'){
        $('input[name=radio_site_type]').attr("disabled",true);
        $('input[name=radio_water]').attr("disabled",true);
    }else{
        $('input[name=radio_site_type]').attr("disabled",false);
        $('input[name=radio_water]').attr("disabled",false);
    }
});

$("input[name='radio_site_type']").on('click', function(){
    $('#flip_to_subtype').val($(this).val());
});

$("input[name='radio_water']").on('click', function(){
    $('#flip_water').val($(this).val());
});

function set_modal_defaults(){
    $("input[name=radio_report_type][value=adult]").prop('checked', true);
    $("input[name=radio_site_type][value=storm_drain]").prop('checked', true);
    $("input[name=radio_water][value=water]").prop('checked', true);
    $('#flip_to_type').val('adult');
    $('#flip_to_subtype').val('storm_drain');
    $('#flip_water').val('water');
    $('input[name=radio_site_type]').attr("disabled",true);
    $('input[name=radio_water]').attr("disabled",true);
}

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-danger.foot_btn.btn_flip', function(){
    const type = $(this).data("type");
    const site_cat = $(this).data("site-cat");
    const report_id = $(this).data("report-id");
    $('#flip_report_id').val( $(this).data("report-id") );
    set_modal_defaults();
    $('#modal_flip_to_site').modal('show');
    /*
    if( type=='adult' ){
        $('#flip_to_type').val( "site" );
        $('#modal_flip_to_site').modal('show');
    }else{
        $('#flip_to_type').val( "adult" );
        const report_id = $(this).data("report-id");
        if(confirm("Site report will be flipped to adult report. Proceed?")){
            flip_report(report_id, 'adult', null);
        }
    }
    */
});

function map_init_basic(map, lat, lon) {
    const mosquito_icon = L.icon({
        iconUrl: iconurl,
        iconSize: [25, 41], // Adjust the size of your icon
        iconAnchor: [12, 41], // Point of the icon that corresponds to marker's location
        popupAnchor: [1, -34], // Point where the popup opens relative to the iconAnchor
    });

    L.marker([ lat, lon ], {icon: mosquito_icon}).addTo(map);
}

function init_maps(){
    $('.maps').each(function(){
        const centerLat = $(this).data('lat');
        const centerLng = $(this).data('lon');
        const map_id = $(this).attr('id');
        try{
            var initialZoom = 6;
            var djoptions = {"layers": [
                        ["OSM", "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                            "\u00a9 <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors"]
                    ],
                        "minimap": false, "scale": "metric", "center": [centerLat, centerLng], "tilesextent": [],
                        "attributionprefix": null, "zoom": initialZoom, "maxzoom": 18, "minzoom": 0, "extent": [
                            [-90,
                                -180],
                            [90,
                                180]
                        ], "resetview": true, "srid": null, "fitextent": true},
                    options = {djoptions: djoptions, globals: false, callback: window.map_init_basic};

            const map = L.Map.djangoMap(map_id, {djoptions: djoptions, globals: false });
            map_init_basic(map, centerLat, centerLng);
        }catch(error){
            console.log(error);
            console.log(map_id);
        };
    });
}

function get_flip_to_subtype(){
    const type = $('input[name="radio_site_type"]:checked').val();
    const water = $('input[name="radio_water"]:checked').val();
    return `${type}_${water}`;
}

$('#go_flip').on('click', function(){
    const report_id = $('#flip_report_id').val();
    const flip_to_type = $('#flip_to_type').val();
    const flip_to_subtype = get_flip_to_subtype();
    //console.log(`${ flip_to_type } ${ site_cat }`);
    //console.log(`${ flip_to_subtype }`);
    flip_report(report_id, flip_to_type, flip_to_subtype);
});

$('#country_select').on('change', function(){
    if($(this).val() != 'all'){
        $('#country_select_exclude').prop('disabled', true);
        $("#country_select_exclude").val("").change();
    }else{
        $('#country_select_exclude').prop('disabled', false);
    }
});

$( "#slider" ).slider({
    min: 0,
    max: 1.05,
    step: 0.05,
    slide: function( event, ui ) {
        $( "#slider_value" ).html( ui.value );
    }
});
$( "#slider" ).slider("value", 1.0);

reset_filter();
load_data();

});