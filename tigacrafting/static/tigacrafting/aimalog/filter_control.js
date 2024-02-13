(function(){

    if (typeof FilterControl === 'undefined') this.FilterControl = {};

    FilterControl.create = function(options){
        return FilterControl;
    }

    FilterControl.write_filter_cookie = function(){
        var cookie_val = JSON.stringify(f.getJson());
        setCookie('alerts_f', cookie_val);
    }

    FilterControl.load_data_to_control = function(control_id, data, id_name, name_name){
        $('#' + control_id).empty();
        var in_html = [];
        in_html.push('<option value="">-----</option>');
        for(var i = 0; i < data.length; i++){
            in_html.push('<option value="' + data[i][id_name] + '">' + data[i][name_name] + '</option>');
        }
        $('#' + control_id).html( in_html.join() );
        $('#' + control_id).prop('disabled', false);
    }

    FilterControl.load_municipalities = function(parent_nuts_code, select_id, id_name, name_name, init_select_val){
        $('#' + select_id + "_spinner").show();
        $.ajax({
            url: '/api/municipalities_below/?nuts_from=' + parent_nuts_code,
            type: "GET",
            dataType: "json",
            success: function(data) {
                FilterControl.load_data_to_control(select_id,data,id_name,name_name);
                $('#' + select_id + "_spinner").hide();
                if(init_select_val != null){
                    $('#' + select_id).val(init_select_val);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
                $('#' + select_id + "_spinner").hide();
            }
        });
    }

    FilterControl.load_nuts_level = function(parent_code, select_id, id_name, name_name, init_select_val){
        $('#' + select_id + "_spinner").show();
        $.ajax({
            url: '/api/nuts_below/?nuts_from=' + parent_code,
            type: "GET",
            dataType: "json",
            success: function(data) {
                FilterControl.load_data_to_control(select_id, data, id_name, name_name);
                $('#' + select_id + "_spinner").hide();
                if(init_select_val!=null){
                    $('#' + select_id).val(init_select_val);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
                $('#' + select_id + "_spinner").hide();
            }
        });
    }

    FilterControl.clear = function(){
        $('#date_from').val( "" );
        $('#date_to').val( "" );
        $('#review_date_from').val( "" );
        $('#review_date_to').val( "" );
        $('#species').val( "" );
        $('#review_species').val( "" );
        $('#status').val( "" );
        $('#review_status').val( "" );
        $('#nuts_0').val( "" );
        $('#all').closest('.btn').button('toggle');
        this.resetAllDropDown();
    }

    FilterControl.getJson = function() {
        var process_filter = $('input[name="processed"]:checked').val();
        if(process_filter==null){
            process_filter = '';
        }
        return {
            date_from : $('#date_from').val(),
            date_to : $('#date_to').val(),
            review_date_from : $('#review_date_from').val(),
            review_date_to : $('#review_date_to').val(),
            species : $('#species').val(),
            review_species : $('#review_species').val(),
            status: $('#status').val(),
            review_status: $('#review_status').val(),
            nuts_0: $('#nuts_0').val(),
            nuts_1: $('#nuts_1').val(),
            nuts_2: $('#nuts_2').val(),
            nuts_3: $('#nuts_3').val(),
            municipality: $('#municipality').val(),
            processed: process_filter
        }
    }

    FilterControl.resetDropDown = function(control_id){
        $('#' + control_id).empty();
        $('#' + control_id).html( '<option value="">-----</option>' );
        $('#' + control_id).prop('disabled', true);
    }

    FilterControl.resetAllDropDown = function(){
        this.resetDropDown('nuts_1');
        this.resetDropDown('nuts_2');
        this.resetDropDown('nuts_3');
        this.resetDropDown('municipality');
    }

    FilterControl.toJson = function(json_data) {
        $('#date_from').val( json_data.date_from );
        $('#date_to').val( json_data.date_to );
        $('#review_date_from').val( json_data.review_date_from );
        $('#review_date_to').val( json_data.review_date_to );
        $('#species').val( json_data.species );
        $('#review_species').val( json_data.review_species );
        $('#status').val( json_data.status );
        $('#review_status').val( json_data.review_status );
        $('#nuts_0').val( json_data.nuts_0 );
        if(json_data.nuts_0 != ''){
            FilterControl.load_nuts_level(json_data.nuts_0,'nuts_1','nuts_id','name_latn', json_data.nuts_1);
        }
        if(json_data.nuts_1 != ''){
            FilterControl.load_nuts_level(json_data.nuts_1,'nuts_2','nuts_id','name_latn', json_data.nuts_2);
        }
        if(json_data.nuts_2 != ''){
            FilterControl.load_nuts_level(json_data.nuts_2,'nuts_3','nuts_id','name_latn', json_data.nuts_3);
        }
        if(json_data.nuts_3 != ''){
            FilterControl.load_municipalities(json_data.nuts_3,'municipality','natcode','nameunit', json_data.municipality);
        }
        if(json_data.processed == null || json_data.processed == ''){
            $('#all').closest('.btn').button('toggle');
        }else{
            $('#' + json_data.processed).closest('.btn').button('toggle');
        }
    }

})();
