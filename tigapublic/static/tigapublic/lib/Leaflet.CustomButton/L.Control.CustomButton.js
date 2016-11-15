/*jshint strict: false */

/*
 * Alexandre Busquets Triola <abusquets@gmail.com>.
 * L.Control.CustomButton is a control to add buttons to Leaflet.
 */

L.Control.CustomButton = L.Control.extend({
    includes: L.Mixin.Events,
    options: {
        container_class: 'leaflet-bar',
        style: 'leaflet-custom-button-el',
        position: 'topleft',
        title: '',
        link: null,
        text: null,
        active: false,
        apply_active_class: true
    },
    // initialize: function(options){
    //     L.Control.prototype.initialize.call(this, options);
    //     this.apply_active_class = true;
    // },
    onAdd: function () {
        this._container = L.DomUtil.create('div',
            this.options.container_class + ' leaflet-control');
        L.DomEvent.disableClickPropagation(this._container);

        this.link = L.DomUtil.create('a', this.options.style, this._container);
        this.link.title = this.options.title;
        if (this.options.link !== null) {
            this.link.href = 'javascript: void(0);';
            if(typeof this.options.link === 'function'){
                L.DomEvent.on(this.link, 'click', this._click_link, this);
            }else{
                L.DomEvent.on(this.link, 'click', function(e){
                    document.location.href = this.options.link;
                    this._stop_propagation(e);
                }, this);
            }
        } else {
            this.link.href = '#';
            L.DomEvent.on(this.link, 'click', this._click, this);
        }
        if (this.options.text !== null) {
            this.link.innerHTML = this.options.text;
        }
        this.active = this.options.active;
        this.active_class();

        return this._container;
    },

    removeFrom: function () {

        if(this._container !== null){
            if (this.options.link !== null) {
                if(typeof this.options.link === 'function'){
                    L.DomEvent.off(this.link, 'click', this._click_link, this);
                }else{
                    L.DomEvent.off(this.link, 'click', function(e){
                        document.location.href = this.options.link;
                        this._stop_propagation(e);
                    }, this);
                }
            } else {
                L.DomEvent.off(this.link, 'click', this._click, this);
            }
            this._container.parentNode.removeChild(this._container);
            this._map = null;
            this._container = null;
        }
        return this;
    },

    active_class: function(){
        if(this.options.apply_active_class === true){
            if(this.active){
                L.DomUtil.addClass(this._container, 'active');
            }else{
                L.DomUtil.removeClass(this._container, 'active');
            }
        }
    },

    _click_link: function (e) {
        this.active = !this.active;
        this.active_class();
        this.options.link(e);
        return this._stop_propagation(e);
    },

    _click: function (e) {
        this.active = !this.active;
        this.active_class();
        this.fire('click', e);
        return this._stop_propagation(e);
    },

    _stop_propagation: function (e) {
        L.DomEvent.stopPropagation(e);
        L.DomEvent.preventDefault(e);
        return false;
    }


});
