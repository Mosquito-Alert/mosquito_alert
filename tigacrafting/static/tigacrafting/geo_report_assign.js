var current_selection;

$(document).ready(function() {

    var geojson;

    var colors = [
        '#FFFFFF',
        '#FFECB8',
        '#FED976',
        '#FEB24C',
        '#FD8D3C',
        '#FC4E2A',
        '#E31A1C',
        '#BD0026',
        '#800026'
    ];

    getcolor = function (gid) {
        var n = count_data[gid]["n"];
        return n > 1000 ? colors[8] : // 1001 - inf
           n > 500  ? colors[7] : // 501 - 1000
           n > 200  ? colors[6] : // 201 - 500
           n > 100  ? colors[5] : // 101 - 200
           n > 50   ? colors[4] : // 51 - 100
           n > 20   ? colors[3] : // 21 - 50
           n > 10   ? colors[2] : // 11 - 20
           n > 0    ? colors[1] : // 1 -10
                      colors[0];  // 0
    };

    style = function(feature){
        return {
            fillColor: getcolor(feature.properties.gid),
            weight: 2,
            opacity: 1,
            color: 'white',
            dashArray: '3',
            fillOpacity: 0.6
        };
    }

    highlightfeature = function(e) {
        var layer = e.target;

        layer.setStyle({
            weight: 5,
            color: '#666',
            dashArray: '',
            fillOpacity: 0.7
        });

        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
            layer.bringToFront();
        }

        info.update(layer.feature.properties.gid);
    };

    resethighlight = function(e){
        geojson.resetStyle(e.target);
		info.update();
    };

    update_current_selection = function(){
        if(current_selection){
            var n_available = count_data[current_selection.gid].n;
            $('#cur_sel').text(current_selection.name + ' - ' + n_available + ' reports available');
            if(n_available > 0){
                $('button.assign').prop("disabled",false);
            }else{
                $('button.assign').prop("disabled",true);
            }
        }else{
            $('#cur_sel').text("None, click on country to select");
        }
    }

    zoomtofeature = function(e) {
		mymap.fitBounds(e.target.getBounds());
		current_selection = { 'gid': e.target.feature.properties.gid , 'name': e.target.feature.properties.name_engl };
		update_current_selection();
	};


    oneachfeature = function(feature, layer) {
		layer.on({
			mouseover: highlightfeature,
			mouseout: resethighlight,
			click: zoomtofeature
		});
	}

    var mymap = L.map('map').setView([40.58, -3.25], 3);

    var osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    var osmAttrib='Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';

    new L.TileLayer(
        osmUrl,
        {minZoom: 2, maxZoom: 12, attribution: osmAttrib}
    ).addTo(mymap);

    geojson = L.geoJson(euro_data, {style:style, onEachFeature: oneachfeature}).addTo(mymap);

    // control that shows state info on hover
	var info = L.control();

	info.onAdd = function (map) {
		this._div = L.DomUtil.create('div', 'info');
		this.update();
		return this._div;
	};

	info.update = function (gid) {
	    var data = count_data[gid];
		this._div.innerHTML = '<h3>Number of pending reports</h3>' +  (gid ? '<b><h4>' + data.name + ' ' + data.n + '</h4></b>' : '<b><h4>Hover over a country</h4></b>');
	};

	info.addTo(mymap);

	var legend = L.control({position: 'bottomright'});

	legend.onAdd = function (map) {

		var div = L.DomUtil.create('div', 'info legend');
		var labels = [];

        labels.push('<i style="background:' + colors[8] + ';"></i>More than 1000');
        labels.push('<i style="background:' + colors[7] + ';"></i>501 - 1000');
        labels.push('<i style="background:' + colors[6] + ';"></i>201 - 500');
        labels.push('<i style="background:' + colors[5] + ';"></i>101 - 200');
        labels.push('<i style="background:' + colors[4] + ';"></i>51 - 100');
        labels.push('<i style="background:' + colors[3] + ';"></i>21 - 50');
        labels.push('<i style="background:' + colors[2] + ';"></i>11 - 20');
        labels.push('<i style="background:' + colors[1] + ';"></i>1 - 10');
        labels.push('<i style="background:' + colors[0] + ';"></i>0');

		div.innerHTML = labels.join('<br>');
		return div;
	};

	legend.addTo(mymap);

	var askforreports = L.control({position: 'topright'});

	askforreports.onAdd = function (map) {
		var div = L.DomUtil.create('div', 'askfor');
		div.innerHTML = '<h3>Current selection</h3><p id="cur_sel">None, click on country to select</p><p><button class="btn btn-danger btn-lg assign">Grab reports <span class="glyphicon glyphicon-download"></span></button></p>';
		return div;
	};

	askforreports.addTo(mymap);

	$('button.assign').click( function(e){
	    var message = "You are about to grab reports from <b>" + current_selection.name + '</b> which currently has <b>' +  count_data[current_selection.gid].n + '</b> reports available. Proceed?'
	    $('#dialog_message').html(message);
        $( "#dialog-confirm" ).dialog('open');
    });

    $('button.assign').prop("disabled",true);

    var get_reports = function(){
        var url = '/api/crisis_report_assign/' + user_id + '/' + current_selection.gid + '/';
        $.ajax({
            url: url,
            type: "POST",
            headers: { "X-CSRFToken": csrf_token },
            success: function( data, textStatus, jqXHR ) {
                $('#loading_progress').html("<p>Done retrieving reports! Going back to EntoLab...");
                window.location.href = '/experts';
            },
            error: function(jqXHR, textStatus, errorThrown){
                $('#loading_progress').hide();
                alert("There has been an error and crisis mode has not been toggled. Please retry later");
            }
        });
    }

    $( "#dialog-confirm" ).dialog({
      resizable: false,
      height: "auto",
      width: 400,
      modal: true,
      autoOpen: false,
      buttons: {
        "Yes": function() {
            $('#loading_progress').show();
            get_reports();
        },
        Cancel: function() {
          $( this ).dialog( "close" );
        }
      }
    });



    /*for(key in count_data){
        var data = count_data[key];
        var marker = new L.marker([data.y,data.x], { opacity: 0.01 }); //opacity may be set to zero
        marker.bindTooltip(data.name + ":" + data.n, {permanent: true, className: "my-label", offset: [0, 0] });
        marker.addTo(mymap);
    }*/
});