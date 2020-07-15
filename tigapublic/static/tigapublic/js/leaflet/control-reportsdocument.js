var MOSQUITO = (function (m) {

    var ReportsDocumentControl = L.Control.SidebarButton.extend({
        options: {
            style: 'leaflet-control-reportsdocument-btn',
            position: 'topleft',
            title: 'leaflet-control-reportsdocument-btn',
            text: '',
            active: false
        },
        getContent: function(){
            var _this = this;
            var container = $('<div>')
              .attr('class', 'sidebar-control-reportsdocument');
            var closeButton = this.getCloseButton().appendTo(container);
            container.append($('#content-control-reportsdocument-tpl').html());
            container.find('button#button-reportsdocument-tpl').click(function(){
                _this.fire('reportsdocument_btn_click');
            });
            return container;
        }
    });

    m.control = m.control || {};
    m.control.ReportsDocumentControl = ReportsDocumentControl;

    return m;

}(MOSQUITO || {}));
