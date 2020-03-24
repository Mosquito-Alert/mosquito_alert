$(".infoPhoto").click(function () {
    //var id = $(this).attr("value").toLowerCase();
    var photoData = [];
    var id = $(this).attr("value");
    url = '/metadataPhotoInfo/?id=' + id

    //var csrftoken = $.cookie('csrftoken');
    $.ajax({
            url: url,
            method: "GET",
            /*beforeSend: function (xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },*/
            dataType: 'json',
            headers: {
                'Authorization': 'Token 7UWSnsNsRBdIgYwfEPeJYWEdeZmRzlh1shlQ'
            },
            success: function( data, textStatus, jqXHR ) {
                console.log("OKAY")
                datos = data.photoData;

                var listacampos = document.createElement("ul");
                var z;
                var str;

                Object.keys(datos).forEach(function(key) {
                    elem = "<li><b>"+ key + "</b>: " + datos[key] +"</li>";
                    listacampos.innerHTML += elem;

                    document.getElementsByClassName("infoPopup")[0].appendChild(listacampos);

                });

                datosCoord = data.photoCoord
                var listacamposTop = document.createElement("ul");



                elem2 = "<li><b>Latitude</b>: " + datosCoord[0]["lat"] +"</li><li><b>Longitude</b>: " + datosCoord[0]["lon"] +"</li>";
                listacamposTop.innerHTML += elem2;
                document.getElementsByClassName("infoPopupTop")[0].appendChild(listacamposTop);




                Object.keys(datosCoord).forEach(function(key) {
                    console.log(key);
                    console.log(datosCoord[key]);
                    elem2 = "<li><b>"+ key + "</b>: " + datosCoord[key] +"</li>";
                    listacamposTop.innerHTML += elem2;

                    document.getElementsByClassName("infoPopupTop")[0].appendChild(listacamposTop);

                });


                $("#infoPhotoDialog").dialog({
                    modal: true,
                    buttons: {
                        "Close": function() {
                            $(this).dialog("close");
                        },
                        /*"No": function() {
                            $(this).dialog("close");
                        }*/
                    },
                    draggable: false,
                    classes: {
                        "ui-dialog": "confirmUpPhoto"
                    }
                });

                $(".ui-dialog").addClass("popupInfoPhoto");


            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(errorThrown);
            }
        });



        /*photoData.forEach(function(key){
            str = document.createElement("li");
            str.innerText = photoData;

            list.appendChild(str);

        });*/

        /*for (z=0; z<photoData.length; z++){
            str = document.createElement("li");
            str.innerText = photoData[z];
            //console.log(str)
            list.appendChild(str);

        }*/

        //








});






/*
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
            });
            */
