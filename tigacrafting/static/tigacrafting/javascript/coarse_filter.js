$(document).ready(function() {

function resetchecks(){
    $('.n_choice').find('span').removeClass('glyphicon');
    $('.n_choice').find('span').removeClass('glyphicon-check');
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
}

function load_data(limit=200, offset=1){
    $('.spinner').show();
    $.ajax({
        url: `/api/coarse_filter_reports/?limit=${limit}&offset=${offset}`,
        type: "GET",
        dataType: "json",
        success: function(data) {
            $('#photo_grid').empty();
            $('.spinner').hide();
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
            console.log(errorThrown);
        },
        cache: false
    });
}

function single_picture_template(picture){
    return `
        <div class="picture_item">
            <img src="${ picture.photo }">
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
                    <button type="button" class="btn btn-primary foot_btn">1</button>
                    <button type="button" class="btn btn-primary foot_btn">2</button>
                    <button type="button" class="btn btn-primary foot_btn">3</button>
                </div>
            </div>
        </div>
    `;
}

$('#next_page_button').click( function(e){
    const offset = $(this).data('offset');
    load_data(200,offset);
} );

$('#previous_page_button').click( function(e){
    const offset = $(this).data('offset');
    load_data(200,offset);
} );

$('#page_button').click( function(e){
    const page = $('#page_input').val();
    if(page != ''){
        load_data(200,parseInt(page));
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
});

/*
function test(){
    const root = $('#photo_grid');
    for(var i = 0; i < data.results.length; i++){
        const report = data.results[i];
        const single_report = single_report_template(report);
        //console.log( single_report );
        root.append(single_report);
    }
}
test();
*/
load_data();

});