$(document).ready(function() {
    $('.exec_val_input').click(function(){
        var control_id_raw = $(this).attr('id');
        var control_id = control_id_raw.replace('vc_executive_','');
        var index = id_to_index[control_id];
        var this_checked = $(this).prop('checked');
        $('#id_form-' + index + '-validation_complete').prop('checked',this_checked);
        $('#id_form-' + index + '-validation_complete_executive').val(this_checked);
    });
});