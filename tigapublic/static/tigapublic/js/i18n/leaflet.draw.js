$(window).ready(function() {
  L.drawLocal = {
	draw: {
		toolbar: {
			// #TODO: this should be reorganized where actions are nested in actions
			// ex: actions.undo  or actions.cancel
			actions: {
				title: t('leaflet.draw.toolbar.cancel.title'),
				text: 'Cancel·lar'
			},
			finish: {
				title: 'Acabar edició',
				text: 'Acabar'
			},
			undo: {
				title: 'Eliminar l\'últim punt creat',
				text: 'Eliminar l\'últim punt'
			},
			buttons: {
				polyline: 'Dibuixar una polilínia',
				polygon: 'Dibuixar un polígon',
				rectangle: 'Dibuixar un rectangle',
				circle: 'Dibuixar un cercle',
				marker: 'Dibuixar un punt'
			}
		},
		handlers: {
			circle: {
				tooltip: {
					start: 'Fes clic i arrossega per dibuixar un cercle.'
				},
				radius: 'Radi'
			},
			marker: {
				tooltip: {
					start: 'Fes clic al mapa per crear un punt.'
				}
			},
			polygon: {
				tooltip: {
					start: t('leaflet.draw.polygon.start'),
					cont: t('leaflet.draw.polygon.continue'),
					end: t('leaflet.draw.polygon.end')
				}
			},
			polyline: {
				error: '<strong>Error:</strong> shape edges cannot cross!',
				tooltip: {
					start: 'Click to start drawing line.',
					cont: 'Click to continue drawing line.',
					end: 'Click last point to finish line.'
				}
			},
			rectangle: {
				tooltip: {
					start: 'Click and drag to draw rectangle.'
				}
			},
			simpleshape: {
				tooltip: {
					end: 'Release mouse to finish drawing.'
				}
			}
		}
	},
	edit: {
		toolbar: {
			actions: {
				save: {
					title: 'Desa els canvis.',
					text: 'Desa'
				},
				cancel: {
					title: 'Cancel·la l\'edició, descarta tots els canvis.',
					text: 'Cancel·la'
				}
			},
			buttons: {
				edit: 'Edit layers.',
				editDisabled: 'No layers to edit.',
				remove: 'Delete layers.',
				removeDisabled: 'No layers to delete.'
			}
		},
		handlers: {
			edit: {
				tooltip: {
					text: 'Drag handles, or marker to edit feature.',
					subtext: 'Click cancel to undo changes.'
				}
			},
			remove: {
				tooltip: {
					text: 'Click on a feature to remove'
				}
			}
		}
	}
};
});
