$(document).ready(function() {
    $('#type_select').on('change', function(e){
        if( $(this).val() == 'adult' ){
            $(".adult").show();
            $(".bite").hide();
            $(".site").hide();
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
    $('#validation_select').on('change', function(e){
        $("." + $(this).val() ).show();
        if( $(this).val() == 'validated' ){
            $('.not_validated').hide();
        }else if ( $(this).val() == 'not_validated' ){
            $('.validated').hide();
        }else{
            $('.all_validated').show();
        }
    });
});