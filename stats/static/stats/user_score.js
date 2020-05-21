var create_dialog = function( report ){
    $(".ui-dialog-content").dialog("close");
    $('#' + report).dialog(
        {
            title:"Report details",
            position: { my: 'top', at: 'top+50' }
        }
    );
};