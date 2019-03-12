var info_window_template =
    '<div class="col-md-4">' +
        '<ul class="list-group">' +
            '<li class="list-group-item">' +
                '<span class="badge">#n_points#</span>' +
                    'Number of points' +
            '</li>' +
            '<li class="list-group-item">' +
                '<span class="badge">#earliest_date#</span>' +
                    'Earliest date' +
            '</li>' +
            '<li class="list-group-item">' +
                '<span class="badge">#latest_date#</span>' +
                    'Latest date' +
            '</li>' +
        '</ul>' +
    '</div>';

$( document ).ready(function() {
    var mymap = L.map('map').setView([37.53097889440026,1.130859375], 5);
    var markers = L.markerClusterGroup();

	L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
		maxZoom: 18,
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
			'<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
			'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		id: 'mapbox.streets'
	}).addTo(mymap);

	var load_data = function(hashtag){
	    $('#info_window').empty();
	    var data_url = '/api/stats/hashtag_map_data/?ht=' + encodeURIComponent(hashtag);
	    $.ajax({
            url: data_url,
            method: "GET",
            success: function( data, textStatus, jqXHR ) {
                console.log(data.stats);
                add_data_to_map(data.data);
                if(data.data.length > 0){
                    var info_html = info_window_template.replace(/#n_points#/g, data.stats.n );
                    info_html = info_html.replace(/#earliest_date#/g, data.stats.earliest_date );
                    info_html = info_html.replace(/#latest_date#/g, data.stats.latest_date );
                    $('#info_window').html(info_html);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(errorThrown);
            }
        });
	}

	var add_data_to_map = function(data){
        markers.clearLayers();
	    latlngs = [];
	    for(var i = 0; i < data.length; i++){
	        var _current = data[i];
	        var marker = L.marker([_current.lat,_current.lon]);

	        var popUpContent = "<p><strong>Note:</strong> " + _current.note + "</p>" +
            "<p><strong>Upload time:</strong> " + _current.date_uploaded + "</p>" +
            "<ul><li>" + _current.picture + "</li></ul>";

	        marker.bindPopup(popUpContent);
	        markers.addLayer(marker);
	        latlngs.push(L.latLng(_current.lat,_current.lon));
	    }

	    mymap.addLayer(markers);

	    if(latlngs.length > 0){
	        var bounds = L.latLngBounds(latlngs);
	        mymap.fitBounds(bounds,{'padding':[100,100]});
	    }
	}

	$( "#load_data" ).click(function() {
        var hashtag = $('#hashtag_input').val();
        load_data(hashtag);
    });

});