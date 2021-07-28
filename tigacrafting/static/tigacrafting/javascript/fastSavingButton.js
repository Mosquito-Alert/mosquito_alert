$( document ).ready(function() {
    $(".preview").each(function (index, element) {
        return hoverPreview($(this)[0]);
    });
});

var array_coincidences = function(array1, array2){
    var filteredArray = array1.filter(function(n) {
        return array2.indexOf(n) !== -1;
    });
    return filteredArray;
};

var save_button = $("#save_button").click(function () {
    var ref = [];
    var other = [];
    var hide_selection = [];
    var illegal_selection_fastload = [];
    var illegal_selection_other = [];

    $("div").removeClass('mustfix');

    $(".fastUploadClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            ref.push($(this).parent().attr('id'));
        }
    });

    $(".hideClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            hide_selection.push($(this).parent().data('id'));
        }
    });

    $(".otherSpeciesClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            other.push($(this).parent().attr('id'));
        }
    });

    illegal_selection_fastload = array_coincidences(ref,hide_selection);
    illegal_selection_other = array_coincidences(other,hide_selection);

    if( illegal_selection_fastload.length == 0 && illegal_selection_other.length == 0){
        if(ref.length>0 || other.length>0){
            if(ref.length>0){
                $('#fastupload_info').show();
            }else{
                $('#fastupload_info').hide();
            }
            if(other.length>0){
                $('#othersp_info').show();
            }else{
                $('#othersp_info').hide();
            }
            $("div").removeClass('mustfix');
            $("#dialogConfirmUpPhoto").dialog({
                modal: true,
                buttons: {
                    "Yes": function() {
                        $("#save_formset").val('T');
                        $("#formset_forms").submit();
                        $(this).dialog("close");
                    },
                    "No": function() {
                        $(this).dialog("close");
                        $(".reportIDs").empty();
                        $(".otherIDs").empty();
                    }
                },
                draggable: false,
                classes: {
                    "ui-dialog": "confirmUpPhoto"
                }
            });

            list_fastupload = [];
            for (var i=0; i<ref.length; i++){
                list_fastupload.push('<li>' + ref[i] + '</li>');
            }

            list_othersp = [];
            for (var i=0; i<other.length; i++){
                list_othersp.push('<li>' + other[i] + '</li>');
            }

            $(".reportIDs").html('<ul>' + list_fastupload.join('') + '</ul>');
            $(".otherIDs").html('<ul>' + list_othersp.join('') + '</ul>');

            $(".ui-dialog").addClass("confirmUpPhoto");

        }else{
            $("#save_formset").val('T');
            $("#formset_forms").submit();

        }
    }else{ //Failed validation, some illegal selections
        $("div").removeClass('mustfix');
        var all_errors = illegal_selection_fastload.concat(illegal_selection_other);
        var all_errors_html = [];
        for(var i = 0; i < all_errors.length; i++){
            all_errors_html.push('<li>' + all_errors[i] + '</li>');
            $("form").find("[data-errorborder='" + all_errors[i] + "']").addClass('mustfix');
        }
        $(".fixids").html('<ul>' + all_errors_html.join('') + '</ul>');
        $("#dialogFix").dialog({
            modal: true,
            buttons: {
                "Ok": function() {
                    $(this).dialog("close");
                }
            },
            draggable: false,
            width: "50%",
            maxWidth: "768px"
        });
    }

});
