//this needs to be called on category change and on value change
var do_translate_classification = function(form_id){
    var form_index = id_to_index[form_id];
    var category = $('#category_' + form_id).find(':selected').val();
    var value = $('#categoryvalue_' + form_id).find(':selected').val()
    var translated_values = translate_table(category,value);
    $('#id_form-' + form_index + '-tiger_certainty_category').val(translated_values['tiger_certainty_category']);
    $('#id_form-' + form_index + '-aegypti_certainty_category').val(translated_values['aegypti_certainty_category']);
}

var translate_table = function( category_id, value ){
    var retVal = { 'tiger_certainty_category': null, 'aegypti_certainty_category': null };
    if( category_id == "4" ){ //albopictus
        retVal['tiger_certainty_category'] = value;
    }else if( category_id == "5" ){ //aegypti
        retVal['aegypti_certainty_category'] = value;
    }else if( category_id == "6" ){ //japonicus
        retVal['tiger_certainty_category'] = -2;
        retVal['aegypti_certainty_category'] = -2;
    }else if( category_id == "7" ){ //koreicus
        retVal['tiger_certainty_category'] = -2;
        retVal['aegypti_certainty_category'] = -2;
    }else if( category_id == "9" ){ //not sure
        retVal['tiger_certainty_category'] = 0;
        retVal['aegypti_certainty_category'] = 0;
    }else if( category_id == "2" ){ //other species
        retVal['tiger_certainty_category'] = -2;
        retVal['aegypti_certainty_category'] = -2;
    }else if( category_id == "8" ){ //complex
        retVal['tiger_certainty_category'] = -2;
        retVal['aegypti_certainty_category'] = -2;
    }else if( category_id == "1" ){ //cannot tell
        retVal['tiger_certainty_category'] = null;
        retVal['aegypti_certainty_category'] = null;
    }
    return retVal;
}


$(document).ready(function () {

    var total_forms = $("#id_form-TOTAL_FORMS").val();
    index_to_id = {};
    id_to_index = {};
    for( var i = 0; i < total_forms; i++){
        index_to_id[i] = $("#id_form-" + i + "-id").val();
        id_to_index[$("#id_form-" + i + "-id").val()] = i;
    }

    $( "select[id^='category_']" ).change(function(e){
        var form_id = e.target.id.split('_')[1];
        var form_index = id_to_index[form_id];
        var needs_value = $(this).find(':selected').data('needs-value');
        //reset everything
        $('#id_form-' + form_index + '-validation_value').val("");
        $('#id_form-' + form_index + '-complex').val("");
        $('#id_form-' + form_index + '-category').val("");
        $('#id_form-' + form_index + '-other_species').val("");
        $('#complex_' + form_id).selectpicker("val","");
        $('#categoryvalue_' + form_id ).selectpicker("val","");
        $('#other_' + form_id ).selectpicker("val","");

        if( needs_value == 1 ){
            $('#container_mix_' + form_id).hide();
            $('#container_value_' + form_id).show();
            $('#container_other_' + form_id).hide();
        }else if( $(this).find(':selected').val() == "2" ){
            $('#container_mix_' + form_id).hide();
            $('#container_value_' + form_id).hide();
            $('#container_other_' + form_id).show();
        }else if ( $(this).find(':selected').val() == "8" ) {
            $('#container_mix_' + form_id).show();
            $('#container_value_' + form_id).hide();
            $('#container_other_' + form_id).hide();
        }else {
            $('#container_mix_' + form_id).hide();
            $('#container_value_' + form_id).hide();
            $('#container_other_' + form_id).hide();
        }
        $('#id_form-' + form_index + '-category').val($(this).find(':selected').val());
        /*if( $(this).find(':selected').val() == "8"){
            $('#id_form-' + form_index + '-category').val("");
        }else{
            $('#id_form-' + form_index + '-category').val($(this).find(':selected').val());
        }*/
        do_translate_classification(form_id);
    });

    $( "select[id^='categoryvalue_']" ).change(function(e){
        var form_id = e.target.id.split('_')[1];
        var form_index = id_to_index[form_id];
        var selected_value = $(this).find(':selected').val();
        $('#id_form-' + form_index + '-validation_value').val(selected_value);
        do_translate_classification(form_id);
    });

    $( "select[id^='complex_']" ).change(function(e){
        var form_id = e.target.id.split('_')[1];
        var form_index = id_to_index[form_id];
        var selected_value = $(this).find(':selected').val();
        $('#id_form-' + form_index + '-complex').val(selected_value);
    });

    $( "select[id^='other_']" ).change(function(e){
        var form_id = e.target.id.split('_')[1];
        var form_index = id_to_index[form_id];
        var selected_value = $(this).find(':selected').val();
        $('#id_form-' + form_index + '-other_species').val(selected_value);
    });
});