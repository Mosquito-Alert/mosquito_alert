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
        this.fetch_data(this.options.bbox, function(data){

            //Toni manipular el rows
            for(var i = 0; i < data.rows.length; i++){

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

    fetch_data: function(bbox, callback){

        $.ajax({
            method: 'GET',
            url: MOSQUITO.config.URL_API + 'reports/' + bbox
        })
        .done(function(resp) {
            callback(resp);
        })
        .fail(function(error) {
            console.log(error);
        });

    },

});
