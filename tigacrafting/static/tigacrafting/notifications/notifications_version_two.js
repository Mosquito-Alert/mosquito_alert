$( document ).ready(function() {
    var SELECTED_SOME_MANUALLY = 0;
    var SELECTED_SOME_FILTER = 1;
    var SELECTED_ALL = 2;

    tinymce.init({
        selector: '#body_en',
        plugins: ["image","code","link"]
    });

    tinymce.init({
        selector: '#body_native',
        plugins: ["image","code","link"]
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
        /*
            {
                'non_push_estimate_num': número de notificacions aprox,
                'push_success': 'ALL' | 'NONE' | 'SOME' | 'NO_PUSH'
                'push_results': List of status
            }
        */
        var pushes = [];
        for(var i = 0; i < data.push_results.length; i++){
            pushes.push('<li>' + JSON.stringify(data.push_results[i]) + '</li>');
        }
        var detail_message = '<ul>' + pushes.join('') + '</ul>';
        var push_message;
        switch(data.push_success){
            case 'ALL':
                push_message = '<li style="color:green;">All pushes sent successfully</li>';
                break;
            case 'NONE':
                push_message = '<li style="color:red;">All pushes failed</li>';
                break;
            case 'SOME':
                push_message = '<li style="color:orange;">Some pushes failed</li>';
                break;
            default:
                push_message = '<li>No push notifications were issued</li>';
                break;
        }
        var message = '<ul>' +
            '	<li><h3>Notifications</h3>' +
            '		<ul>' +
            '			<li style="color:green;">Estimated number of recipients: '+ data.non_push_estimate_num +'</li>' +
            '		</ul>' +
            '	</li>' +
            '	<li><h3>Push</h3>' +
            '		<ul>' + push_message + '</ul>' +
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
        var body_html_en_editor_content = tinyMCE.get('body_en').getContent();
        var title_en = $("#title_en").val();
        return body_html_en_editor_content == '' || body_html_en_editor_content == '' || title_en == '';
    }
    validate_data = function(){
        /*
            error conditions
            - title_en or body_html_en missing
            - sent to single user and no tokens selected
            - sent to group and no topic selected
            - missing one or more native fields (missing all is ok)
        */
        var retVal = {
            'validation': true,
            'errors': []
        };
        var title_en = $("#title_en").val();
        if(title_en == null || title_en == ''){
            retVal.validation = false;
            retVal.errors.push('<li class="text-danger">Missing english title text</li>')
        }
        var body_html_en_editor_content = tinyMCE.get('body_en').getContent();
        if(body_html_en_editor_content == ''){
            retVal.validation = false;
            retVal.errors.push('<li class="text-danger">Missing english body text</li>')
        }
        var body_html_native_editor_content = tinyMCE.get('body_native').getContent();
        var title_native = $("#title_native").val();
        var selected_native_locale = $('#native_lang').val()

        if( body_html_native_editor_content != "" || title_native != "" || selected_native_locale != "" ){
            if( body_html_native_editor_content == "" ){
                retVal.validation = false;
                retVal.errors.push('<li class="text-danger">Missing native body text</li>')
            }
            if( title_native == "" ){
                retVal.validation = false;
                retVal.errors.push('<li class="text-danger">Missing native title text</li>')
            }
            if(selected_native_locale == ""){
                retVal.validation = false;
                retVal.errors.push('<li class="text-danger">Missing native locale</li>')
            }

        }

        if(get_selected_tokens() == '' && $("#accordion").accordion( "option", "active" ) == 0){
            retVal.validation = false;
            retVal.errors.push('<li class="text-danger">No user uuids selected in manual selection</li>')
        }
        if($("#accordion").accordion( "option", "active" ) == SELECTED_SOME_FILTER && no_topic_selected()){
            retVal.validation = false;
            retVal.errors.push('<li class="text-danger">No topics selected in choose filter</li>')
        }
        return retVal;
    };
    $( "#save_button" ).click(function() {
        var validation_result = validate_data();
        if(!validation_result.validation){
            $('#dialog-message-validation').empty();
            $('#dialog-message-validation').html("<p>You can't send the notification(s) yet because:</p><ul>" + validation_result.errors.join("") + "</ul><p>Correct these problems and try again please.</p>")
            $('#dialog-message-validation').dialog('open');
        }else{
            ajax_post_notification_content();
        }
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
        ppush = get_push();

        some_data.recipients = recipients;
        some_data.notification_content_id = content_id;
        some_data.user_id = user_id;
        some_data.ppush = ppush;

        return some_data;
    };
    jsonify_notification_content = function(){
        var data = {};
        var body_html_en = tinyMCE.get('body_en').getContent();
        var body_html_native = tinyMCE.get('body_native').getContent();
        var title_en = $('#title_en').val();
        var title_native = $('#title_native').val();

        data.body_html_en = body_html_en;
        if(body_html_native != ''){
            data.body_html_native = body_html_native;
        }
        data.title_en = title_en;
        if(title_native != ''){
            data.title_native = title_native;
        }
        var native_code_lang = $('#native_lang').val();
        if(native_code_lang != ''){
            data.native_locale = native_code_lang;
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
        $('.ui-slider').slider('disable');
        $.ajax({
            type: "GET",
            url: '/api/user_count/?filter_criteria=' +  encodeURIComponent(select_op),
            dataType: 'json',
            headers: { "X-CSRFToken": csrf_token },
            success: function(data){
                set_message_user_count("Message will be sent to " + data.user_count + " users");
                $('#number_estimate_text').removeClass("progress");
                $('.ui-slider').slider('enable');
            },
            error: function(jqXHR, textStatus, errorThrown){
                set_message_user_count("Error estimating number of users: " + jqXHR.responseText);
                $('#number_estimate_text').removeClass("progress");
                $('.ui-slider').slider('enable');
            }
        });
    }
    set_message_user_count = function(message){
        $('#number_estimate_text').html(message);
    };
    get_selected_radio_op = function(){
        var selected = $('#topic').val();
        return selected;
    };
    $('input[type=radio][name=criteriarb]').change(function() {
        var selected = $(this).attr('id');
        if (selected!='score_arbitrary'){
            ajax_number_users(selected);
        }else{
            ranges = $('#amount').val();
            min = ranges.split('-')[0].trim();
            max = ranges.split('-')[1].trim();
            ajax_number_users(selected + '-' + min + '-' + max);
        }

    });
    clear_criteria = function(){
        $('#number_estimate').hide();
        $('.radioop').prop('checked', false);
    };
    no_topic_selected = function(){
        if($('#topic').val() != ""){
            return false;
        }
        return true;
    }
    criteria_is_unchecked = function(){
        var retVal = true;
        $('.radioop').each(function(){
            if($(this).prop('checked')==true){
                retVal = false;
            }
        });
        return retVal;
    };
    if(user_uuid!=''){
        $('.tokenize-user-uuid').tokenize2().trigger('tokenize:tokens:add', [user_uuid, user_uuid, true]);
    }
    $( "#slider-range" ).slider({
        range: true,
        min: 0,
        max: 100,
        values: [ 95, 100 ],
        slide: function( event, ui ) {
            $( "#amount" ).val( ui.values[ 0 ] + " - " + ui.values[ 1 ] );
        },
        stop: function( event, ui ) {
            if (get_selected_radio_op().startsWith("score_arbitrary")){
                ajax_number_users("score_arbitrary" + "-" + ui.values[ 0 ] + "-" + ui.values[ 1 ])
            }
        }
    });

    var init_groups = function(){
        $('#topic_group').empty();
        var elems = ['<option value="">-----</option>'];
        for(var i = 0; i < topics_info.length; i++){
            var elem = '<option value="' + topics_info[i].topic_group_value + '">' + topics_info[i].topic_group_text + '</option>'
            elems.push(elem);
        }
        $('#topic_group').html( elems.join() );
    }

    var init_topics = function(data){
        $('#topic').empty();
        var elems = ['<option value="">-----</option>'];
        for(var i=0; i < data.length; i++){
            var elem = '<option value="' + data[i].topic_value + '">' + data[i].topic_text + '</option>'
            elems.push(elem);
        }
        $('#topic').html( elems.join() );
    }

    init_groups();

    $('#topic_group').change(function(e){
        var value = $(this).val();
        var index = parseInt(value);
        if(value == ''){
            init_topics([]);
        }else{
            init_topics(topics_info[index].topics);
        }
    });

    var clear_topic = function(){
        $('#topic_group').val("");
        init_topics([]);
    }

    var clear_everything = function(){
        clear_topic();
        clear_tokens();
        $("#radio-1").prop("checked", true);
        $("#accordion").accordion("option","active",0);
        $("#title_en").val("");
        $("#title_native").val("");
        $("#native_lang").val("");
        if(tinymce.get('body_en')){
            tinymce.get('body_en').setContent('');
        }
        if(tinymce.get('body_native')){
            tinymce.get('body_native').setContent('');
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
    clear_everything();
});