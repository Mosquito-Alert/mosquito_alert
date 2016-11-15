
var MOSQUITO = (function (m) {

    var ReportsDocumentControl = L.Control.CustomButton.extend({
        'apply_active_class': false
    });

    m.control = m.control || {};
    m.control.ReportsDocumentControl = ReportsDocumentControl;

    return m;

}(MOSQUITO || {}));
