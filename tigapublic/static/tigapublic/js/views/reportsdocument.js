var ReportsdocumentView = BaseView.extend({
    el: '#page-reports',
    initialize: function(options) {
        options = options || {};
        this.scope = {};
        this.templates = {};

        this.options = _.extend({}, this.defaults, options);
        this.tpl = _.template($('#content-reportsdocument-tpl').text());
        this.render();

    },

    render: function() {
        var _this = this;
        this.fetch_data(this.options, function(data){

            //Toni manipular el rows
            for(var i = 0; i < data.rows.length; i++){
                row = data.rows[i];

                if (row.observation_date !== null &&
                    row.observation_date !== '' ){
                        var theDate = new Date(row.observation_date * 1000);
                        row.observation_date = theDate.getDay() + '-' + (theDate.getMonth() + 1) + '-' + theDate.getFullYear();
                }

                if(row.expert_validation_result !== null &&
                    row.expert_validation_result.indexOf('#') !== -1){
                    row.expert_validation_result = row.expert_validation_result.split('#');
                    row.expert_validation_result_specie = row.expert_validation_result[0];
                    if ( row.expert_validation_result_specie == 'site'){
                        row.titol_capa = 'site';
                    } else if ( row.expert_validation_result[1] == 1 ) {
                        row.titol_capa = row.expert_validation_result_specie +'_probable';
                    } else if (row.expert_validation_result[1] == 2){
                        row.titol_capa = row.expert_validation_result_specie +'_seguro';
                    } else if (row.expert_validation_result[1] == 0){
                        row.titol_capa = 'unidentified';
                    } else{
                        row.titol_capa = 'other_species';
                    }
                }
            }

            _this.$el.html(_this.tpl(data));
            window.t().translate(MOSQUITO.lng, _this.$el);

            var row, center, map;
            for(i = 0; i < data.rows.length; i++){
                row = data.rows[i];

                center  = [row.lat, row.lon];
                map = L.map('map_report_' + row.id, { zoomControl:false}).
                    setView(center, 16);

                L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
                        maxZoom: 18,
                        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                    }).addTo(map);
                L.marker(center).addTo(map);
            }

        });
        return this;

    },

    fetch_data: function(options, callback){

        $.ajax({
            method: 'GET',
            url: MOSQUITO.config.URL_API + 'reports/' + options.bbox //+ '/' + options.year + '/' + options.months + '/-' + options.excluded_types
        })
        .done(function(resp) {
            callback(resp);
        })
        .fail(function(error) {
            console.log(error);
        });

    },

});
