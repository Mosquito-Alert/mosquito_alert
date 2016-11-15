// From https://github.com/openstreetmap/openstreetmap-website/blob/4cad1970fbd15d455ad231d7e75a400344fc9e02/app/assets/javascripts/leaflet.sidebar.js
/*
Modified by Alexandre Busquets Triola <abusquets@gmail.com>
*/
L.OSM = L.OSM || {};
L.OSM.sidebar = function(selector) {
  var control = {},
    sidebar = $(selector),
    current = $(),
    currentButton  = $(),
    map;

  control.addTo = function (_) {
    map = _;
    return control;
  };

  control.addPane = function(pane) {
    pane
      .hide()
      .appendTo(sidebar);
  };

  control.closePane = function() {
      if($(sidebar).is(':visible')){
          control.togglePane(this.lastPane, this.lastButton);
      }
  }

  control.togglePane = function(pane, button) {

    this.lastPane = pane;
    this.lastButton = button;

    current
      .hide()
      .trigger('hide');

    currentButton
      .removeClass('active');

    if (current === pane) {
      $(sidebar).hide();
      current = currentButton = $();
    } else {
      $(sidebar).show();
      current = pane;
      currentButton = button || $();
    }

    current
      .show()
      .trigger('show');

    //map.invalidateSize({pan: false, animate: false});


    currentButton
      .addClass('active');

    if(current[0]){
        current.parent().attr('data-sidebar-panel',
            current.attr('class').split(' ')[0]);
    }


  };

  return control;
};
