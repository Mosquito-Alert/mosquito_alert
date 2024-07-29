$(document).ready(function() {
    $('#type_select').on('change', function(e){
        if( $(this).val() == 'adult' || $(this).val() == 'all' ){
            //$('#validation_select option[value="all_validated"]').attr("selected", true);
            $('#validation_select').attr('disabled', false);
        }else{
            $('#validation_select').val("all_validated");
            $('#validation_select').attr('disabled', true);
        }
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

    function map_init_basic(map, lat, lon) {
        const mosquito_icon_class = L.Icon.Default.extend({
            options: { iconUrl: iconurl }
        });
        const mosquito_icon = new mosquito_icon_class;
        L.marker([ lat, lon ], {icon: mosquito_icon}).addTo(map);
    }

    function init_maps(){
        $('.maps').each(function(){
            const centerLat = $(this).data('lat');
            const centerLng = $(this).data('lon');
            const map_id = $(this).attr('id');
            var initialZoom = 6;
            var djoptions = {"layers": [
                        ["OSM", "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                            "\u00a9 <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors"]
                    ],
                        "minimap": false, "scale": "metric", "center": [centerLat, centerLng], "tilesextent": [],
                        "attributionprefix": null, "zoom": initialZoom, "maxzoom": 18, "minzoom": 0, "extent": [
                            [-90,
                                -180],
                            [90,
                                180]
                        ], "resetview": true, "srid": null, "fitextent": true},
                    options = {djoptions: djoptions, globals: false, callback: window.map_init_basic};

            const map = L.Map.djangoMap(map_id, {djoptions: djoptions, globals: false });
            map_init_basic(map, centerLat, centerLng);
        });
    }

    init_maps();
});