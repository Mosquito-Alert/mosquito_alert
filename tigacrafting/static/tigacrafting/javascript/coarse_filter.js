$(document).ready(function() {

function reset_filter(){
    $('#visibility_select').val('visible');
    $('#type_select').val('all');
    $('#country_select').val('all');
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
    const ia_threshold = $('#slider').slider('value');
    const note = escape($('#usernote_filter').val());
    return `
        {
            "visibility": "${visibility}",
            "visibility_readable": "${visibility_readable}",
            "report_type": "${report_type}",
            "report_type_readable": "${report_type_readable}",
            "country": "${country}",
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
    $('.current').html(`Page ${current_page} of ${n_pages} (${n_total} reports)`);
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
            $('#' + report_id).remove();
        },
        error: function(jqXHR, textStatus, errorThrown){
            $('#' + report_id).unblock();
        },
        cache: false
    });
}

function load_data(limit=200, offset=1, q=''){
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
            <img src="http://webserver.mosquitoalert.com${ picture.photo }" width="100" height="100" >
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
    const ia_value = report.ia_filter_1 == null ? 'N/A' : report.ia_filter_1;
    const additional_button_class = report.type == 'site' ? 'hide_button' : '';
    return `
        <div id="${ report.version_UUID }" class="photo ${ report.type } ${ site_cat }">
            <div class="photo_internal_wrapper">
                <div class="header_internal_wrapper">
                    <div class="header_country">
                        <a href="/single_simple/${ report.version_UUID }" target="_blank"><span class="glyphicon glyphicon-link" style="color: white;"> ${ report_country_name }</span></a>
                    </div>
                    <div class="header_ia">
                        IA Value ${ ia_value }
                        <div id="ia${ report.version_UUID }" data-ia-value="${ report.ia_filter_1 }" data-type="${ report.type }" data-id="${ report.version_UUID }" class="ia_graph ${report.type}" style=""></div>
                    </div>
                </div>
                <hr class="hrnomargin">
                <div class="body_internal_wrapper">
                    <p><span class="label label-success">Report id</span> ${ report.version_UUID }</p>
                    <p><span class="label label-success">Date</span> ${ report.creation_time }</p>
                    <p><span class="label label-success">User Notes</span> ${ report.note } </p>
                </div>
                <hr>
                <div class="pictures_internal_grid_wrapper">
                    <div class="pictures_internal_grid">
                        ${ pictures }
                    </div>
                </div>
                <hr class="hrnomargin">
                <div class="buttons_internal_grid">
                    <button type="button" title="Hide report" data-report-id="${ report.version_UUID }" class="btn btn-primary foot_btn btn_hide_report">Hide</button>
                    <button type="button" title="Other species" data-category="2" data-report-id="${ report.version_UUID }" class="${ additional_button_class } btn btn-primary foot_btn btn_other">O.species</button>
                    <button type="button" title="Probably culex" data-report-id="${ report.version_UUID }" class="${ additional_button_class } btn btn-primary foot_btn btn_pculex">P.culex</button>
                    <button type="button" title="Probably albopictus" data-report-id="${ report.version_UUID }" class="${ additional_button_class } btn btn-primary foot_btn btn_palbo">P.albo.</button>
                    <button type="button" title="Definitely albopictus" data-report-id="${ report.version_UUID }" class="${ additional_button_class } btn btn-primary foot_btn btn_dalbo">D.albo.</button>
                    <button type="button" title="Not sure" data-report-id="${ report.version_UUID }" class="${ additional_button_class } btn btn-primary foot_btn btn_notsure">N.S.</button>
                </div>
            </div>
        </div>
    `;
}

$('#next_page_button').click( function(e){
    const offset = $(this).data('offset');
    const page_size = get_page_size();
    load_data(page_size,offset);
} );

$('#previous_page_button').click( function(e){
    const offset = $(this).data('offset');
    const page_size = get_page_size();
    load_data(page_size,offset);
} );

$('#page_button').click( function(e){
    const page = $('#page_input').val();
    const page_size = get_page_size();
    if(page != ''){
        load_data(page_size,parseInt(page));
    }
    console.log(page);
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
    //console.log(filter);
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

$('div#photo_grid').on('click', 'div.buttons_internal_grid button.btn.btn-primary.foot_btn.btn_other', function(){
    console.log('click');
    const category_id = $(this).data("category");
    const report_id = $(this).data("report-id");
    classify_picture(report_id, category_id, null);
});

$( "#slider" ).slider({
    min: -1,
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