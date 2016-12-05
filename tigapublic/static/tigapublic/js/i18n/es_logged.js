var trans = trans || {};

add = {
    'layer.trash_layer': 'Otras observaciones',

    'map.controlmoreinfo_desc_es': '<ul class="info_list"> \
        <li><b>'+t('layer.tiger')+'</b>: Según los expertos, las fotos de esta observación podrían ser de mosquito tigre (<i>Aedes albopictus</i>). \
          <p>Si se ven muy claramente sus rasgos taxonómicos, especialmente la raya blanca en cabeza y tórax, será “confirmado”. Si no se aprecian algunos rasgos, será “posible”.</p> \
        </li> \
        <li><b>'+t('layer.zika')+'</b>: Según los expertos, las fotos de esta observación podrían ser de mosquito de la fiebre amarilla (<i>Aedes aegypti</i>). \
          <p>Si se ven muy claramente sus rasgos taxonómicos, especialmente la lira en cabeza y tórax, será “confirmado”. Si no se aprecian algunos rasgos, será “posible”.</p> \
        </li> \
        <li><b>'+t('layer.other_species')+'</b>: Según los expertos, las fotos de esta observación podrían ser de otras especies de mosquito.</li> \
        <li><b>'+t('layer.unidentified')+'</b>: Según los expertos, estas observaciones y sus fotos no permiten identificar a ninguna especie de mosquito.</li> \
        <li><b>'+t('layer.unclassified')+'</b>: Observaciones con foto que aún no han sido validadas por expertos.</li> \
        <li><b>'+t('layer.site')+'</b>: Observaciones ciudadanas de posibles lugares de cría (imbornales y otros) de mosquito tigre o de la fiebre amarilla. Incluye observaciones que aún no han sido filtradas por expertos.</li> \
        <li><b>Otras observaciones</b>: Observaciones que no corresponden a ninguna otra categoría pero que podrían contener información de interés para gestores.</li> \
        <li><b>'+t('layer.userfixes')+'</b>: Los cuadros más oscuros indican que hay más personas con la app instalada o bien que hay usuarios que han estado mucho tiempo con la app en su móvil.</li> \
      </ul> \
      <p>Para saber más sobre los métodos de clasificación consultar <a href="http://www.mosquitoalert.com/mapa-y-resultados/mapa" target="blank">www.mosquitoalert.com/mapa-y-resultados/mapa</a></p> \
      <p>Más información del proyecto en <a href="http://www.mosquitoalert.com" target="blank">www.mosquitoalert.com</a></p>',

    'map.control_download':'Descargar datos',
    'map.download_btn':'Descargar datos',
    'map.text_description_download': '<p>La descarga se realizará a partir de los elementos que se visualizan en el mapa. Comprueba que estén activas las capas de la leyenda que deseas así como los filtros temporales y el nivel de zoom.</p><p>Una vez definida la vista deseada pulsa en el botón de descarga.</p>',
    'map.title_download': 'Descarga',

    'map.controlshare_view_description': 'Comparte esta vista privada',
    'share.private_layer_warn': '¡Atención! La vista que vas a compartir contiene los siguientes datos privados:()Solo los usuarios registrados tendrán acceso a esta vista.',

};
_.extend(trans.es, add);
