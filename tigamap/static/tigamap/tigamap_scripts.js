    			function loadSavedLat() {
					var gotCookieString = getCookie("myMapCookie");
					var splitStr = gotCookieString.split("_");
					var savedMapLat = parseFloat(splitStr[0]);
					return savedMapLat;
				}

				function loadSavedLng() {
					var gotCookieString = getCookie("myMapCookie");
					var splitStr = gotCookieString.split("_");
					var savedMapLng = parseFloat(splitStr[1]);
					return savedMapLng;
				}

				function loadSavedZoom() {
					var gotCookieString = getCookie("myMapCookie");
					var splitStr = gotCookieString.split("_");
					var savedMapZoom = parseFloat(splitStr[2]);
					return savedMapZoom;
				}


				function getCookie(c_name) {
					var i, x, y, ARRcookies = document.cookie.split(";");
					for ( i = 0; i < ARRcookies.length; i++) {
						x = ARRcookies[i].substr(0, ARRcookies[i].indexOf("="));
						y = ARRcookies[i].substr(ARRcookies[i].indexOf("=") + 1);
						x = x.replace(/^\s+|\s+$/g, "");
						if (x == c_name) {
							return unescape(y);
						}
					}
					return "";
				}

   				function saveMapState(map) {
					var mapZoom = map.getZoom();
					var mapCentre = map.getCenter();
					var mapLat = mapCentre.lat;
					var mapLng = mapCentre.lng;
					var cookiestring = mapLat + "_" + mapLng + "_" + mapZoom;
                    var d = new Date();
                    d.setTime(d.getTime() + (exdays*24*60*60*1000));
                    var expires = "expires="+d.toGMTString();
					document.cookie = "tigaMapCookie" + "=" + cookiestring + ";expires=" + expires + ";domain=tigaserver.atrapaeltigre.com;path=/";
				}

