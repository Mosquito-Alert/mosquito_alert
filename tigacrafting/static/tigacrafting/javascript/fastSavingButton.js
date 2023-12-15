$( document ).ready(function() {
    $(".preview").each(function (index, element) {
        return hoverPreview($(this)[0]);
    });
    $('.hideClass').change(function() {
        var id = $(this).parent().data('id');
        if( $(this).prop('checked') ){
            $('*[data-id="' + id + '"]').each(function (index, element) {
                if(!$(this).attr("class").startsWith("hide_check")){
                    var check = $(this).find("input");
                    check.prop('checked', false);
                }
            });
        }
    });
    $('.otherSpeciesClass').change(function() {
        var id = $(this).parent().data('id');
        if( $(this).prop('checked') ){
            $('*[data-id="' + id + '"]').each(function (index, element) {
                if(!$(this).attr("class").startsWith("other_sp")){
                    var check = $(this).find("input");
                    check.prop('checked', false);
                }
            });
        }
    });
    $('.probablyCulexClass').change(function() {
        var id = $(this).parent().data('id');
        if( $(this).prop('checked') ){
            $('*[data-id="' + id + '"]').each(function (index, element) {
                if(!$(this).attr("class").startsWith("probably_culex")){
                    var check = $(this).find("input");
                    check.prop('checked', false);
                }
            });
        }
    });
    $('.probablyAlbopictusClass').change(function() {
        var id = $(this).parent().data('id');
        if( $(this).prop('checked') ){
            $('*[data-id="' + id + '"]').each(function (index, element) {
                if(!$(this).attr("class").startsWith("probably_albopictus")){
                    var check = $(this).find("input");
                    check.prop('checked', false);
                }
            });
        }
    });
    $('.sureAlbopictusClass').change(function() {
        var id = $(this).parent().data('id');
        if( $(this).prop('checked') ){
            $('*[data-id="' + id + '"]').each(function (index, element) {
                if(!$(this).attr("class").startsWith("sure_albopictus")){
                    var check = $(this).find("input");
                    check.prop('checked', false);
                }
            });
        }
    });
    $('.fastUploadClass').change(function() {
        var id = $(this).parent().data('id');
        if( $(this).prop('checked') ){
            $('*[data-id="' + id + '"]').each(function (index, element) {
                if(!$(this).attr("class").startsWith("fastCheck")){
                    var check = $(this).find("input");
                    check.prop('checked', false);
                }
            });
        }
    });
    $('.notSureClass').change(function() {
        var id = $(this).parent().data('id');
        if( $(this).prop('checked') ){
            $('*[data-id="' + id + '"]').each(function (index, element) {
                if(!$(this).attr("class").startsWith("not_sure")){
                    var check = $(this).find("input");
                    check.prop('checked', false);
                }
            });
        }
    });
});

var save_button = $("#save_button").click(function () {
    var ref = [];

    $(".fastUploadClass").each(function (index, element) {
        if ($(this).prop("checked")) {
            ref.push($(this).parent().data('id'));
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