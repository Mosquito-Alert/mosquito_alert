$( document ).ready(function() {
    var SELECTED_SOME_MANUALLY = 0;
    var SELECTED_SOME_FILTER = 1;
    var SELECTED_ALL = 2;

    tinymce.init({
        selector: '#body_es',
        plugins: ["image","code","link","fullpage"]
    });
    tinymce.init({
        selector: '#body_ca',
        plugins: ["image","code","link","fullpage"]
    });
    tinymce.init({
        selector: '#body_en',
        plugins: ["image","code","link","fullpage"]
    });
    $('.tokenize-user-uuid').tokenize2({
        dropdownMaxItems: 15,
        searchMinLength: 3,
        dataSource: function(term, object){
            $.ajax('/api/users/', {
                data: { user_UUID: term, start: 0 },
                dataType: 'json',
                success: function(data){
                    var $items = [];
                    $.each(data, function(k, v){
                        $items.push({"text":v.user_UUID,"value":v.user_UUID});
                    });
                    object.trigger('tokenize:dropdown:fill', [$items]);
                }
            });
        }
    });
    format_report = function(data){
        var notifications_failed = data.notifications_failed;
        var notifications_issued = data.notifications_issued;
        var push_issued_android = data.push_issued_android;
        var push_failed_android = data.push_failed_android;
        var push_issued_ios = data.push_issued_ios;
        var push_failed_ios = data.push_failed_ios;
        var message = '<ul>' +
            '	<li><h3>Notifications</h3>' +
            '		<ul>' +
            '			<li style="color:green;">Success:'+ notifications_issued +'</li>' +
            '			<li style="color:red;">Fail:'+ notifications_failed +'</li>' +
            '		</ul>' +
            '	</li>' +
            '	<li><h3>Push</h3>' +
            '		<ul>' +
            '			<li><h4>Android</h4>' +
            '				<ul>' +
            '					<li style="color:green;">Success:'+ push_issued_android +'</li>' +
            '					<li style="color:red;">Fail:'+ push_failed_android +'</li>' +
            '				</ul>' +
            '			</li>' +
            '			<li><h4>IOS</h4>' +
            '				<ul>' +
            '					<li style="color:green;">Success:' + push_issued_ios + '</li>' +
            '					<li style="color:red;">Fail:' + push_failed_ios + '</li>' +
            '				</ul>' +
            '			</li>' +
            '		</ul>' +
            '	</li>' +
            '</ul>';
            return message;
    };

    ajax_post_send_notifications = function(notificationcontent_id){
        notification_data = jsonify_notification(notificationcontent_id);
        $('#gear').show();
        $.ajax({
            type: "PUT",
            url: '/api/send_notifications/',
            dataType: 'json',
            headers: { "X-CSRFToken": csrf_token },
            data: notification_data,
            success: function(data){
                $('#gear').hide();
                $("#dialog-message-report-text").html(format_report(data));
                $("#dialog-message-report").dialog("open");
            },
            error: function(jqXHR, textStatus, errorThrown){
                $('#gear').hide();
                $("#dialog-message-error-text").html(jqXHR.responseText);
                $("#dialog-message-error").dialog("open");
            }
        });
    }
    ajax_post_notification_content = function(){
        this_data = jsonify_notification_content();
        $.ajax({
            type: "PUT",
            url: '/api/notification_content/',
            dataType: 'json',
            headers: { "X-CSRFToken": csrf_token },
            data: this_data,
            success: function(data){
                var notificationcontent_id = data.id;
                ajax_post_send_notifications(notificationcontent_id);
            },
            error: function(jqXHR, textStatus, errorThrown){
                $("#dialog-message-error-text").html(jqXHR.responseText);
                $("#dialog-message-error").dialog("open");
            }
        });
    };
    some_field_in_tinymce_is_missing = function(){
        var body_html_es_editor_content = tinyMCE.get('body_es').getContent();
        var body_html_ca_editor_content = tinyMCE.get('body_ca').getContent();
        var body_html_en_editor_content = tinyMCE.get('body_en').getContent();
        var title_es = $("#title_es").val();
        var title_ca = $("#title_ca").val();
        var title_en = $("#title_en").val();
        return body_html_es_editor_content == '' || body_html_ca_editor_content == '' || body_html_en_editor_content == '' || title_es == '' ||  title_ca == '' || title_en == '';
    }
    validate_data = function(){
        var title_es = $("#title_es").val();
        if(title_es == null || title_es == ''){
            return false;
        }
        var body_html_es_editor_content = tinyMCE.get('body_es').getContent();
        if(body_html_es_editor_content == ''){
            return false;
        }
        if(get_selected_tokens() == '' && $("#accordion").accordion( "option", "active" ) == 0){
            return false;
        }
        if($("#accordion").accordion( "option", "active" ) == SELECTED_ALL && some_field_in_tinymce_is_missing){
            return false;
        }
        if($("#accordion").accordion( "option", "active" ) == SELECTED_SOME_FILTER && criteria_is_unchecked()){
            return false;
        }
        return true;
    };
    $( "#save_button" ).click(function() {
        if(!validate_data()){
            $('#dialog-message-validation').dialog('open');
        }else{
            ajax_post_notification_content();
        }
    });

    var clear_everything = function(){
        clear_criteria();
        clear_tokens();
        $("#accordion").accordion("option","active",0);
        $("#radio-1").prop("checked", true);
        $("#title_es").val("");
        $("#title_ca").val("");
        $("#title_en").val("");
        if(tinymce.get('body_es')){
            tinymce.get('body_es').setContent('');
        }
        if(tinymce.get('body_ca')){
            tinymce.get('body_ca').setContent('');
        }
        if(tinymce.get('body_en')){
            tinymce.get('body_en').setContent('');
        }
    };

    $( "#clear_form" ).click(function() {
        $('<div></div>').appendTo('body')
            .html('<div><h6>Proceed?</h6></div>')
            .dialog({
                modal: true,
                title: 'The form will be cleared and all fields will be set to default state',
                zIndex: 10000,
                autoOpen: true,
                width: 600,
                resizable: false,
                buttons: {
                    Yes: function () {
                        clear_everything();
                        $(this).dialog("close");
                    },
                    No: function () {
                        $(this).dialog("close");
                    }
                },
                close: function (event, ui) {
                    $(this).remove();
                }
            });
    });
    $('#gear').hide();
    $( "#accordion" ).accordion({
        heightStyle: "content",
        activate: function( event, ui ) {
            var selected = $(this).accordion( "option", "active" );
            if(selected == SELECTED_ALL){
                clear_tokens();
                clear_criteria();
            }else if(selected == SELECTED_SOME_MANUALLY){
                clear_criteria();
            }else if(selected == SELECTED_SOME_FILTER){
                clear_tokens();
            }
        }
    });
    get_selected_tokens = function(){
        data = [];
        $('.token').each(function(index,value){
            data.push($(value).attr('data-value'));
        });
        return data.join("$");
    };
    get_push = function(){
        return $('input[name=rb]:checked').attr('id') == 'radio-1';
    }
    clear_tokens = function(){
        $('.token').each(function(index,value){
            $(value).remove();
        });
    };
    jsonify_notification = function(content_id){
        var some_data = {};
        var selected = $( "#accordion" ).accordion( "option", "active" );
        if(selected==SELECTED_ALL){
            recipients = "all";
        }else if(selected==SELECTED_SOME_MANUALLY){
            recipients = get_selected_tokens();
        }else{
            recipients = get_selected_radio_op();
        }
        report_id = "42e2521d-9e08-4ad6-82da-7d8e0b68e960";
        ppush = get_push();

        some_data.recipients = recipients;
        some_data.notification_content_id = content_id;
        some_data.user_id = user_id;
        some_data.report_id = report_id;
        some_data.ppush = ppush;

        return some_data;
    };
    jsonify_notification_content = function(){
        var data = {};
        var body_html_es = tinyMCE.get('body_es').getContent();
        var body_html_ca = tinyMCE.get('body_ca').getContent();
        var body_html_en = tinyMCE.get('body_en').getContent();
        var title_es = $('#title_es').val();
        var title_ca = $('#title_ca').val();
        var title_en = $('#title_en').val();
        data.body_html_es = body_html_es;
        if(body_html_ca != ''){
            data.body_html_ca = body_html_ca;
        }
        if(body_html_en != ''){
            data.body_html_en = body_html_en;
        }
        data.title_es = title_es;
        if(title_ca != ''){
            data.title_ca = title_ca;
        }
        if(title_en != ''){
            data.title_en = title_en;
        }
        return data;
    };
    $( "#dialog-message-error" ).dialog({
        modal: true,
        autoOpen: false,
        buttons: {
            Ok: function() {
                $( this ).dialog( "close" );
            }
        }
    });
    $( "#dialog-message-report" ).dialog({
        modal: true,
        autoOpen: false,
        buttons: {
            Ok: function() {
                $( this ).dialog( "close" );
            }
        }
    });
    $( "#dialog-message-validation" ).dialog({
        modal: true,
        autoOpen: false,
        width: 400,
        buttons: {
            Ok: function() {
                $( this ).dialog( "close" );
            }
        }
    });
    ajax_number_users = function(select_op){
        $('#number_estimate').show();
        $('#number_estimate_text').addClass("progress");
        set_message_user_count("Estimating number of messages...");
        $.ajax({
            type: "GET",
            url: '/api/user_count/?filter_criteria=' + select_op,
            dataType: 'json',
            headers: { "X-CSRFToken": csrf_token },
            success: function(data){
                set_message_user_count("Message will be sent to " + data.user_count + " users");
                $('#number_estimate_text').removeClass("progress");
            },
            error: function(jqXHR, textStatus, errorThrown){
                set_message_user_count("Error estimating number of users: " + jqXHR.responseText);
                $('#number_estimate_text').removeClass("progress");
            }
        });
    }
    set_message_user_count = function(message){
        $('#number_estimate_text').html(message);
    };
    get_selected_radio_op = function(){
        var selected = $('input[type=radio][name=criteriarb]:checked').attr('id');
        return selected;
    };
    $('input[type=radio][name=criteriarb]').change(function() {
        var selected = $(this).attr('id');
        ajax_number_users(selected);
    });
    clear_criteria = function(){
        $('#number_estimate').hide();
        $('.radioop').prop('checked', false);
    };
    criteria_is_unchecked = function(){
        var retVal = true;
        $('.radioop').each(function(){
            if($(this).prop('checked')==true){
                retVal = false;
            }
        });
        return retVal;
    };
    $("#radio-1").prop("checked", true);
    clear_everything();
    if(user_uuid!=''){
        $('.tokenize-user-uuid').tokenize2().trigger('tokenize:tokens:add', [user_uuid, user_uuid, true]);
    }
});