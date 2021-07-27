$( document ).ready(function() {
    $(".preview").each(function (index, element) {
        return hoverPreview($(this)[0]);
    });
});

var save_button = $("#save_button").click(function () {
    var ref = [];
    var other = [];

    $(".fastUploadClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            ref.push($(this).parent().attr('id'));
        }
    });

    $(".otherSpeciesClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            other.push($(this).parent().attr('id'));
        }
    });

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

});
