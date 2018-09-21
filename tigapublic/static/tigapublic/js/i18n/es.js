var trans = trans || {};
trans.es = {
    //TO DELETE?
    'map.si': 'Sí',
    'map.no': 'No',
    'map.no_confirmado': 'Seguro que no',
    'map.no_posible': 'No lo parece',
    'map.si_posible': 'Posible',
    'map.si_confirmado': 'Confirmado',
    'map.no_answers': '-',
    'map.site_water': 'Imbornales con agua',
    'map.site_dry': 'Imbornales sin agua',
    'map.site_other': 'Otros',
    'map.site_pending': 'Por filtrar',
    'hashtag.filters.placeholder': 'Por #hashtag',
    'check_notifications': 'Notificaciones',
    'info.notifications': 'Notificaciones',

    //header
    'header.login': 'Login',
    'header.logout': 'Logout',
    'header.username': 'Usuario',
    'header.password': 'Clave',
    'header.submit': 'Aceptar',
    'header.motto': 'Observaciones ciudadanas',
    'header.logo_url': "window.open('http://www.mosquitoalert.com')",

    //COOKIE
    'map.cookie_consent': 'Este sitio web utiliza cookies. Si continuas navegando asumimos tu permiso para utilizarlas.'+
      '<br/>Para más información sobre las políticas del sitio web, por favor consulta nuestra <a href="http://webserver.mosquitoalert.com/es/privacy/">Política de privacidad</a> y <a href="http://webserver.mosquitoalert.com/es/terms/">Acuerdo del usuario</a>.',
    'map.cookie_accept': 'Cerrar notificación',

    //GENERALITIES
    'title': 'Título',
    'error.unknown': 'Ocurrió un error',
    'remove': 'Eliminar',
    'display-example': 'Ver ejemplo',

    //TOC
    'group.observations':'Observaciones ciudadanas',
    'group.userfixes':'Distribución de participantes',
    'group.breeding_sites':'Lugares de cría',
    'group.userdata':'Capas de usuario',
    'group.filters':'Filtros',
    'layer.mosquito_tiger_probable': 'Posible mosquito tigre',
    'layer.mosquito_tiger_confirmed': 'Mosquito tigre confirmado',
    'layer.yellow_fever_confirmed': 'Mosquito fiebre amarilla confirmado',
    'layer.yellow_fever_probable': 'Posible mosquito fiebre amarilla',
    'layer.unidentified': 'No identificable',
    'layer.breeding_site_other': 'Lugares de cría',
    'layer.breeding_site_not_yet_filtered': 'Lugares de cría',
    'layer.storm_drain_dry': 'Lugares de cría',
    'layer.storm_drain_water': 'Lugares de cría',
    'layer.other_species': 'Otras especies',
    'layer.userfixes': 'Distribución de participantes',
    'layer.filtered': 'Filtrado',

    'layer.tiger': 'Mosquito tigre',
    'layer.zika': 'Mosquito fiebre amarilla',
    'layer.site': 'Lugares de cría',

    //MAP CONTROLS
    'map.numfixes': 'Observaciones',
    'map.control_layers': 'Leyenda',
    'map.control_moreinfo': 'Más información acerca de la leyenda',
    'map.control_share': 'Compartir',
    'map.control_viewreports': 'Listado de observaciones',

    'map.controlshare_share': 'Compartir',
    'map.controlshare_share_description': 'Comparte el sitio web',
    'map.controlshare_view_description': 'Comparte la vista de este mapa',
    'map.controlshare_home': 'Proyecto',
    'map.controlshare_view': 'Vista',

    //MAP FILTERS
    'All years': 'Todos los años',
    'All months': 'Todos los meses',
    'January': 'Enero',
    'February': 'Febrero',
    'March': 'Marzo',
    'April': 'Abril',
    'May': 'Mayo',
    'June': 'Junio',
    'July': 'Julio',
    'August': 'Agosto',
    'September': 'Septiembre',
    'October': 'Octubre',
    'November': 'Noviembre',
    'December': 'Diciembre',

    'map.controlmoreinfo_title': 'Descripción',
    'map.mundial_controlmoreinfo_title': 'Descripción',

    'citizeninfo.tiger_mosquito': ' Según los ciudadanos y ciudadanas, las fotos de esta observación podrían ser de mosquito tigre (<i>Aedes albopictus</i>).',
    'citizeninfo.yellow_fever_mosquito':' Según los ciudadanos y ciudadanas, las fotos de esta observación podrían  ser de mosquito de la fiebre amarilla (<i>Aedes aegypti</i>).',
    'citizeninfo.other_species':' Según los ciudadanos y ciudadanas, las fotos de esta observación podrían  ser de otras especies de mosquito.',
    'citizeninfo.unidentify': ' Según los ciudadanos y ciudadanas, estas observaciones y sus fotos no permiten identificar a ninguna especie de mosquito.',
    'citizeninfo.site': 'Observaciones ciudadanas de posibles lugares de cría (imbornales) de mosquito tigre o de la fiebre amarilla.',
    'map.to_know_more':'Para saber más sobre los métodos de clasificación consultar <a href="http://www.mosquitoalert.com/mapa-y-resultados/mapa" target="blank">www.mosquitoalert.com/mapa-y-resultados/mapa</a>',
    'map.more_info':'Más información del proyecto en <a href="http://www.mosquitoalert.com" target="blank">www.mosquitoalert.com</a>',

    'expertinfo.tiger_mosquito': ' Según los expertos, las fotos de esta observación podrían ser de mosquito tigre (<i>Aedes albopictus</i>).',
    'expertinfo.yellow_fever_mosquito':' Según los expertos, las fotos de esta observación podrían ser de mosquito de la fiebre amarilla (<i>Aedes aegypti</i>).',
    'expertinfo.other_species':' Según los expertos, las fotos de esta observación podrían ser de otras especies de mosquito.',
    'expertinfo.unidentify': ' Según los expertos, estas observaciones y sus fotos no permiten identificar a ninguna especie de mosquito.',
    'expertinfo.site': 'Observaciones ciudadanas de posibles lugares de cría (imbornales) de mosquito tigre o de la fiebre amarilla.',
    'expertinfo.userfixes':'Los cuadros más oscuros indican que hay más personas con la app instalada o bien que hay usuarios que han estado mucho tiempo con la app en su móvil.',

    'map.controldocumentsreport_title': 'Listado de observaciones',
    'map.controldocumentsreport_desc': '<p>Informe de las observaciones que se visualizan en la vista actual del mapa (máximo 300).</p><p>Verifica el número de observaciones con el contador de puntos mostrados en el margen inferior izquierdo de la vista del mapa.</p>',
    'map.viewreports_btn': 'Ver selección',
    'map.report_title': 'Observación',

    'map.user_note':'Nota ciudadana: ',
    'map.expert_note':'Nota experta: ',
    'map.versio_informe': 'Código observación',
    'map.observation_date': 'Fecha',
    'map.longitud': 'Longitud',
    'map.latitud': 'Latitud',
    'map.coordenadas': 'Coordenadas (latitud,longitud)',
    'map.breeding_site_answers': 'Lugar de cría',
    'map.expert_validated': 'Validación experta: ',
    'map.citizen_validated': 'Validación ciudadana: ',
    'map.showed_reports': 'Puntos mostrados:',

    'map.multi_report_title': 'Mosquito Alert: Listado de observaciones',
    'map.anonim': 'Anónimo',
    'map.share_social_text': 'Mira este mapa de @MosquitoAlert #cienciaciudadana',

    'share.look_at': 'Mira el mapa de @Mosquito_Alert #MosquitoTigre #CienciaCiudadana',

    'report.author': 'Autor',
    'report.license': 'Licencia: ',
    'report.license_text':'<b>Licencia</b>: El uso de los datos y obras de este portal privado está restringido únicamente a acciones profesionales de seguimiento y control del mosquito tigre y del mosquito de la fiebre amarilla. Ni los datos ni las obras (imágenes) de este visor privado y sus descargas o exportaciones no pueden cederse a terceros, ni ser publicados en ningún formato ni medio, ni usados para ningún otro fin, sin el consentimiento expreso del equipo coordinador de Mosquito Alert.',

    'error.invalid_login': 'No hay ningún usuario con estas credenciales.',
    'error.no_points_selected': 'No hay ningún punto.',
    'error.too_many_points_selected': 'Hay demasiados puntos.',

    // Descarga de datos
    'map.control_download':'Descargar datos',
    'map.download_btn':'Descargar datos',
    'map.text_description_download': '<p>La descarga se realizará a partir de los elementos que se visualizan en el mapa. Comprueba que estén activas las capas de la leyenda que deseas así como los filtros temporales y el nivel de zoom.</p><p>Una vez definida la vista deseada pulsa en el botón de descarga.</p>',
    'map.title_download': 'Descarga',

    //Draw. Not visible when defined in es_logged
    'leaflet.draw.polygon.start': 'Marca la posición del primer punto en el mapa.',
    'leaflet.draw.polygon.continue': 'Sigue dibujando el contorno del polígono.',
    'leaflet.draw.polygon.end': 'Marca el primer punto (o haz doble clic en un nuevo punto) para terminar.',

    //NOTIFICACIONES
    'with_my_notifications': 'Con mis notificaciones',
    'without_my_notifications': 'Sin mis notificaciones',
    'all_notifications': 'Con/sin mis notificaciones',
    'map.notification.type.filters.title': 'Por tipo de notificación',

    // NEW
    'notification.warning.municiaplities': 'Solo es posible enviar notificaciones a las observaciones hechas en municipios vinculados al usuario de esta sesión.',
    'group.filters.time': 'Filtros temporales',
    'group.filters.hashtag': 'Filtro por #hashtag',
    'group.filters.notifications': 'Filtros por notificaciones',
    'group.filters.municipalities': 'Filtro por municipio',
    'group.filters.time.custom_daterange': 'Fecha personalizada',
    'group.filters.time.apply': 'Filtra',
    'group.filters.time.clear': 'Borra',
    'group.filters.time.cancel': 'Cierra',
    'general.next': 'Siguiente',
    'general.previous': 'Anterior',
    'general.shortday.sunday': 'Do',
    'general.shortday.monday': 'Lu',
    'general.shortday.tuesday': 'Ma',
    'general.shortday.wednesday': 'Mi',
    'general.shortday.thursday': 'Ju',
    'general.shortday.friday': 'Vi',
    'general.shortday.saturday': 'Sa',
    'general.today': 'Hoy',
    'general.yesterday': 'Ayer',
    'general.before_yesterday': 'Anteayer',
    'group.filters.shortcut.this_week': 'Esta semana',
    'group.filters.shortcut.last_7_days': 'Últimos 7 días',

    'filter.municipality.placeholder': 'Búsqueda de municipios',
    'filter.municipalities.inputtooshort': 'Mínimo 2 caracteres',
    'label.user-municipalities': 'Mis municipios',

    // MODELS
    'layer.predictionmodels': 'Probabilidad Mosquito Tigre',
    //HTML FORMAT
    'layer.predictionmodels.description': 'El mapa muestra la probabilidad media de alerta de mosquito tigre (valores de 0 a 1), en una cuadrícula de 4x4 Km, clasificados en 4 niveles de incertidumbre derivados de las desviaciones estándares asociadas a nuestras estimaciones medias. Estos niveles de incertidumbre representan la probabilidad de que un participante envíe al menos, una fotografía confiable de un mosquito tigre desde una determinada celda de la cuadrícula de 4x4 Km durante las dos semanas precedentes al día en cuestión, controlando por el esfuerzo de muestreo.<p>Estas probabilidades en su mayoría dependen de la distribución de las poblaciones de mosquito tigre y de la época del año (ya que estas especies tienen un ciclo estacional con variaciones en su abundancia poblacional). El modelo, publicado en Nature Communications 8:916 (2017), controla el esfuerzo de muestreo y ha demostrado que produce estimaciones similares a las que se pueden realizar a partir de trampas de ovoposición de mosquito. Este modelo estacional que no incluye aún información climática ni ambiental se ejecuta una vez a la semana generando estimaciones diarias.</p>',
    'models.label.prob-1': 'Muy baja',
    'models.label.prob-2': 'Baja',
    'models.label.prob-3': 'Media',
    'models.label.prob-4': 'Alta',
    'models.label.sd-1': 'Muy baja',
    'models.label.sd-2': 'Baja',
    'models.label.sd-3': 'Media',
    'models.label.sd-4': 'Alta',
    'models.probability': 'Probabilidad',
    'models.uncertainty': 'Incertidumbre',

    'general.year': 'Año',
    'general.month': 'Mes',
};
