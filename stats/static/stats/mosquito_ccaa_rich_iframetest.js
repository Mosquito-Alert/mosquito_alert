var getCheckedCategories = function(){
    var checked_list = [];
    var categories = ['confirmed','probable','other','unidentified'];
    for(var i = 0; i < categories.length; i++){
        var checked = $('#' + categories[i]).prop('checked');
        if(checked){
            checked_list.push(categories[i]);
        }
    }
    return checked_list;
}

var showPanel = function(category){
    var checked_categories = getCheckedCategories();
    var filter_array = [];
    for( var i = 0; i < checked_categories.length; i++){
        filter_array.push('#' + checked_categories[i]);
    }
    filter_string = filter_array.join(',');
    if(filter_string != ''){
        $grid.isotope({ filter: filter_string });
    }else{
        $grid.isotope({ filter: '#kk' });
    }
}

var hideLoader = function(div_id){
    $('#' + div_id + " .progress").hide();
}

$( document ).ready(function() {
//$(function () {

    $grid = $('.grid').isotope({
        layoutMode: 'fitRows',
        itemSelector: '.grid-item'
    });
    $grid.isotope({ filter: '#kk' });

    $("#categories").append('<li><input id="confirmed" onclick="javascript:showPanel(\'confirmed\')" type="checkbox">Mosquit tigre confirmat</li>');
    $("#categories").append('<li><input id="probable" onclick="javascript:showPanel(\'probable\')" type="checkbox">Mosquit tigre probable</li>');
    $("#categories").append('<li><input id="other" onclick="javascript:showPanel(\'other\')" type="checkbox">Altres espècies</li>');
    $("#categories").append('<li><input id="unidentified" onclick="javascript:showPanel(\'unidentified\')" type="checkbox">No identificats</li>');

    $('#confirmed_iframe').attr('src','/stats/mosquito_ccaa_rich/confirmed');
    $('#probable_iframe').attr('src','/stats/mosquito_ccaa_rich/probable');
    $('#other_iframe').attr('src','/stats/mosquito_ccaa_rich/other');
    $('#unidentified_iframe').attr('src','/stats/mosquito_ccaa_rich/unidentified');

    $("#confirmed_iframe").on('load',function(){
        hideLoader('confirmed');
    });

    $("#probable_iframe").on('load',function(){
        hideLoader('probable');
    });

    $("#other_iframe").on('load',function(){
        hideLoader('other');
    });

    $("#unidentified_iframe").on('load',function(){
        hideLoader('unidentified');
    });

});