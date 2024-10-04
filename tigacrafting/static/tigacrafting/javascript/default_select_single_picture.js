$( document ).ready(function() {
    // When loading page, check all photo blocks
    $('.photo_wrapper').each(function(){
      //If there is a single photo
      if($(this).children('[id^=div_for_photo_to_display_report]').length == 1){
        //And it has a visible radio button
        if ($(this).children('[id^=div_for_photo_to_display_report]').is(":visible")){
          var elem = $(this).children('[id^=div_for_photo_to_display_report]')[0];
          // check it
          $(elem.children[0]).prop('checked',true);
        }
      }
    });
});