var create_dialog = function( report ){
    $(".ui-dialog-content").dialog("close");
    $('#' + report).dialog(
        {
            title:"Info",
            position: { my: 'top', at: 'top+50' }
        }
    );
};