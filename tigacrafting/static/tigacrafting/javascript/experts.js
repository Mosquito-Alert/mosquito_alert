$(".infoPhoto").click(function () {
    console.log($(this).attr("value"));

    var id = $(this).attr("value").toLowerCase();

    url = '/metadataPhotoInfo/?id=' + id
    console.log(url);
    //var csrftoken = $.cookie('csrftoken');
    $.ajax({
            url: url,
            method: "GET",
            /*beforeSend: function (xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },*/

            success: function( data, textStatus, jqXHR ) {
                console.log("OKAY")
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(errorThrown);
            }
        });







            /*$.ajax({
                url: 'http://{{ domain }}/api/coverage/?id_range_start=' + id_start + '&id_range_end=' + id_stop,
                contentType: 'application/json',
                dataType: 'json',
                headers: {
                    'Authorization': 'Token 7UWSnsNsRBdIgYwfEPeJYWEdeZmRzlh1shlQ'
                },
                beforeSend: function (xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                },
                success: function (data) {

                    if (data != null && data.length > 0) {

                        $.each(data, function (index, value) {
                            if (value != null && value.lat != null && value.lon != null && value.n_fixes != null) {

                                L.polygon([
                                    [value.lat, value.lon],
                                    [value.lat + 0.05, value.lon],
                                    [value.lat + 0.05, value.lon + 0.05],
                                    [value.lat, value.lon + 0.05]
                                ], {weight: 0.5, opacity: 1, color: color, fillOpacity: make_opacity(value.n_fixes), fillColor: color}).bindPopup(make_popup_text(value.n_fixes), popup_options).addTo(map);

                            }
                        });

                    }
                    percent_done = Math.floor(100 * id_stop /{{ last_id }});
                    progress_bar.css("width", percent_done.toString() + "%");
                    if (percent_done > 10) {
                        progress_bar.html(percent_done.toString() + "%");
                    }
                    if (percent_done >= 100) {
                        progress_bar_container.fadeOut(2000);
                    }
                }
            });*/




    /*$("#infoPhotoDialog").dialog({
        modal: true,
        buttons: {
            "Yes": function() {
                //$("#save_formset").val('T');
                //$("#formset_forms").submit();
                $(this).dialog("close");
                alert("yes");
            },
            "No": function() {
                $(this).dialog("close");
                //$(".reportIDs li").remove();
                alert("no");
            }
        },
        draggable: false,
        classes: {
            "ui-dialog": "confirmUpPhoto"
        }
    });*/



});
