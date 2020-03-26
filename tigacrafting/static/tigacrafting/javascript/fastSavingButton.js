var save_button = $("#save_button").click(function () {
    var cont = 0;
    var ref = new Array();
    var i = 0;

    $(".fastUploadClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            cont = cont + 1;
            ref.push($(this).parent().attr('id'));
        }
    });


    if(cont>0){
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
            //console.log(ref[z]);
            str = document.createElement("li");
            str.innerText = ref[z];
            //console.log(str)
            list.appendChild(str);
        }

        document.getElementsByClassName("reportIDs")[0].appendChild(list);

        $(".ui-dialog").addClass("confirmUpPhoto");

    }else{
        $("#save_formset").val('T');
        $("#formset_forms").submit();

    }
});
