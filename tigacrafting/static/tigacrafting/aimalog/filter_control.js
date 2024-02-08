(function(){

    if (typeof FilterControl === 'undefined') this.FilterControl = {};

    FilterControl.create = function(options){
        return FilterControl;
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
        this.resetAllDropDown();
    }

    FilterControl.getJson = function() {
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
            nuts_3: $('#nuts_3').val()
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
        $('#nuts_1').val( json_data.nuts_1 );
        $('#nuts_2').val( json_data.nuts_2 );
        $('#nuts_3').val( json_data.nuts_3 );
    }

})();
