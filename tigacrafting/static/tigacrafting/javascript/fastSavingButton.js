var save_button = $("#save_button").click(function () {
    var cont = 0;
    var ref = new Array();
    var i = 0;
    //console.log($(".reportID").text());

    $(".fastUploadClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            cont = cont + 1;
        }

        console.log(i);
        console.log($("#id_form-" + i + "-fastUpload.fastUploadClass").prop('checked'));
        console.log("id_form-" + i + "-fastUpload.fastUploadClass");
        console.log($( "#id_form-" + i + "-fastUpload.fastUploadClass").parent().attr('id'));
        if($("#id_form-" + i + "-fastUpload.fastUploadClass").prop('checked')){
            ref.push($( "#id_form-" + i + "-fastUpload.fastUploadClass").parent().attr('id'));
        }
        i++;

        //ref.push($("#id_form-"+ i +"-version_UUID").val());
        //console.log($( "#id_form-" + i + "-fastUpload.fastUploadClass").parent());
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

        /*for (i=0; i<=ref.length; i++){
            $('.reportIDs').html(ref[i]);
            $('.reportIDs').createElement("br");
        }*/


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

        //list.appendChild(str);
        //console.log(list)
        document.getElementsByClassName("reportIDs")[0].appendChild(list);

        $(".ui-dialog").addClass("confirmUpPhoto");

    }else{
        $("#save_formset").val('T');
        $("#formset_forms").submit();

    }
});
