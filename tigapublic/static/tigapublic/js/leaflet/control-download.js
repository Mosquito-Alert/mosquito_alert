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
            var closeButton = this.getCloseButton().appendTo(container);
            container.append($('#content-control-download-tpl').html());
            container.find('.download_button button').click(function(){
                _this.fire('download_btn_click');
            });
            return container;
        }
    });

    m.control = m.control || {};
    m.control.ControlDownload = ControlDownload;

    return m;

}(MOSQUITO || {}));
