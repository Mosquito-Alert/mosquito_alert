$(".infoPhoto").click(function () {
    $("#infoPhotoDialog").dialog({
        modal: true,
        buttons: {
            "Yes": function() {
                $("#save_formset").val('T');
                $("#formset_forms").submit();
                $(this).dialog("close");
            },
            "No": function() {
                $(this).dialog("close");
                $(".reportIDs li").remove()
            }
        },
        draggable: false,
        classes: {
            "ui-dialog": "confirmUpPhoto"
        }
    });



});
