
var MOSQUITO = (function (m) {

    var CustomDIV = L.Control.extend({
        //includes: L.Mixin.Events,
        options: {
            style: 'leaflet-custom-div-el',
            position: 'bottomleft',
            content: '#content#'
        },

        onAdd: function () {
            this._container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            L.DomEvent.disableClickPropagation(this._container);
            this.el = L.DomUtil.create('div', this.options.style, this._container);
            this.setContent();
            return this._container;
        },

        removeFrom: function () {

            if(this._container !== null){
                this._container.parentNode.removeChild(this._container);
                this._map = null;
                this._container = null;
            }
            return this;
        },

        setContent: function (content) {
            var text = '';
            if(content !== undefined){
                text = content;
            }else{
                text = this.options.content;
            }
            this.el.innerHTML = text;
        }

    });

    m.control = m.control || {};
    m.control.CustomDIV = CustomDIV;

    return m;

}(MOSQUITO || {}));
