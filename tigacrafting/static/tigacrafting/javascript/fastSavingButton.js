var save_button = $("#save_button").click(function () {
    var cont = 0;
    $(".fastUploadClass").each(function () {
        if ($(this).prop("checked")) {
            cont = cont + 1;
        }
    });

    if(cont>0){
        $("#instruc").dialog({
            modal: true,
            buttons: {
                "Acceptar": function() {
                    $("#save_formset").val('T');
                    $("#formset_forms").submit();
                    $(this).dialog("close");
                },
                "Cancelar": function() {
                    $(this).dialog("close");
                }
            },
            draggable: false,
            classes: {
                "ui-dialog": "popupInstrucciones"
            }
        });

        $(".ui-dialog").addClass("popupInstrucciones");

    }else{
        alert("No ventana");
    }
});
