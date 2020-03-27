$(".infoPhoto").click(function () {
    //var id = $(this).attr("value").toLowerCase();
    var photoData = [];
    var id_photo_report = $(this).attr("value");

    var aux = id_photo_report.split("__");
    var id = aux[0]
    var id_photo = aux[1]

    url = '/metadataPhotoInfo/?id=' + id + '&id_photo=' + id_photo

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

                if(data.noData){
                    var warningNoData = document.createElement("p");
                    elemNoData = "<p>"+ data.noData +"</p>";
                    warningNoData.innerHTML += elemNoData;

                    document.getElementsByClassName("infoNoData")[0].appendChild(warningNoData);

                    $("#noDataAvailable").dialog({
                        modal: true,
                        height: 200,
                        width: 450,

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

                }else{
                    datos = data.photoData;
                    var listacampos = document.createElement("ul");
                    var z;
                    var str;

                    Object.keys(datos).forEach(function(key) {
                        elem = "<li><b>"+ key + "</b>: " + datos[key] +"</li>";
                        listacampos.innerHTML += elem;

                        document.getElementsByClassName("infoPopup")[0].appendChild(listacampos);

                    });

                    if(data.photogpsData){
                        datosGPS = data.photogpsData;
                        var listacamposGPS = document.greateElement("ul");

                        Object.keys(datosGPS).forEach(function(key) {
                            elemGPS = "<li><b>"+ key + "</b>: " + datosGPS[key] +"</li>";
                            listacamposGPS.innerHTML += elemGPS;
                            document.getElementsByClassName("infoPopupGPS")[0].appendChild(listacamposGPS);
                        });

                    }

                    if(data.photoCoord || data.photoDateTime){
                        var listacamposTop = document.createElement("ul");


                        if (data.photoCoord){
                            datosCoord = data.photoCoord
                            elem2 = "<li><b>Latitude</b>: " + datosCoord[0]["lat"] +"</li><li><b>Longitude</b>: " + datosCoord[0]["lon"] +"</li>";
                            listacamposTop.innerHTML += elem2;

                        }

                        if (data.photoDateTime){
                            dataDateTime = data.photoDateTime
                            elem3 = "<li><b>Date Time: </b> " + dataDateTime[0]["DateTime"] + "</li>"
                            listacamposTop.innerHTML += elem3;
                            //document.getElementsByClassName("infoPopupTop")[0].appendChild(listacamposTop);
                        }

                        document.getElementsByClassName("infoPopupTop")[0].appendChild(listacamposTop);

                    }

                    $("#infoPhotoDialog").dialog({
                        modal: true,
                        height: 700,
                        width: 450,

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
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(errorThrown);
            }
        });
});
