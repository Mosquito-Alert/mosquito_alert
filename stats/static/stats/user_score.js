var create_dialog = function( report ){
    $(".ui-dialog-content").dialog("close");
    $('#' + report).dialog({"title":"Report details"});
};