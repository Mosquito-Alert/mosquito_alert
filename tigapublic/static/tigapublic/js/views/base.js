var BaseView = Backbone.View.extend({
    close: function () {
    console.log('Closing view ' + this);
        if (this.beforeClose) {
            this.beforeClose();
        }
        this.remove();
        this.unbind();
    }
});
