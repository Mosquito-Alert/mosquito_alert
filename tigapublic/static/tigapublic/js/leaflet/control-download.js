var MOSQUITO = (function (m) {

    var ControlDownload = L.Control.SidebarButton.extend({
        options: {
            style: 'leaflet-control-download-btn',
            position: 'topleft',
            title: 'leaflet-control-download-btn',
            text: 'D',
            active: false
        },
        getContent: function(){
            var _this = this;
            var container = $('<div>')
              .attr('class', 'sidebar-control-download');
            container.html($('#content-control-download-tpl').html());
            container.find('button').click(function(){
                _this.fire('download_btn_click');
            });
            return container;
        }
    });

    m.control = m.control || {};
    m.control.ControlDownload = ControlDownload;

    return m;

}(MOSQUITO || {}));
