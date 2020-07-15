var BaseView = Backbone.View.extend({
    close: function () {
        if (this.beforeClose) {
            this.beforeClose();
        }
        this.remove();
        this.unbind();
    },
    "isMobile": function() {
      return L.Browser.mobile;
    }
});

function bufferedBounds(leafletGeometry, distance){
    leafletGeometry._northEast.lat+=distance;
    leafletGeometry._northEast.lng+=distance;
    leafletGeometry._southWest.lat-=distance;
    leafletGeometry._southWest.lng-=distance;
    return leafletGeometry;

}

String.prototype.ucfirst = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}
