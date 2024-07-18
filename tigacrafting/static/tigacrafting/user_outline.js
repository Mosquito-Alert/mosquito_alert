$(document).ready(function() {
    $('#type_select').on('change', function(e){
        if( $(this).val() == 'adult' ){
            $(".site").hide();
            $(".bite").hide();
            $(".adult").show();
        }else if( $(this).val() == 'site' ){
            $(".adult").hide();
            $(".bite").hide();
            $(".site").show();
        }else if( $(this).val() == 'bite' ){
            $(".adult").hide();
            $(".bite").show();
            $(".site").hide();
        }else{
            $(".adult").show();
            $(".bite").show();
            $(".site").show();
        }
    });
});