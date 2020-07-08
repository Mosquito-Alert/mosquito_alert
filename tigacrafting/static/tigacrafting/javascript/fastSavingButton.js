var save_button = $("#save_button").click(function () {
    var ref = [];

    $(".fastUploadClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            ref.push($(this).parent().attr('id'));
        }
    });

    if(ref.length>0){
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
                    $(".reportIDs li").remove()
                }
            },
            draggable: false,
            classes: {
                "ui-dialog": "confirmUpPhoto"
            }
        });

        var list = document.createElement("ul");
        var z;
        var str;

        for (z=0; z<ref.length; z++){
            str = document.createElement("li");
            str.innerText = ref[z];
            list.appendChild(str);
        }

        document.getElementsByClassName("reportIDs")[0].appendChild(list);

        $(".ui-dialog").addClass("confirmUpPhoto");

    }else{
        $("#save_formset").val('T');
        $("#formset_forms").submit();

    }
});
