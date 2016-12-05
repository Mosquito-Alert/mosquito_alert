var trans = trans || {};

add = {
    'layer.trash_layer': 'Altres observacions',

    'map.controlmoreinfo_desc_es': '<ul class="info_list"> \
        <li><b>'+t('layer.tiger')+'</b>: Segons els experts, les fotos d\'aquesta observació podrien ser de mosquit tigre (<i>Aedes albopictus</i>). \
          <p>Si es veuen molt clarament els seus trets taxonòmics, especialment la ratlla blanca al cap i tòrax, serà "confirmat". Si no s\'aprecien alguns trets, serà "possible".</p> \
        </li> \
        <li><b>'+t('layer.zika')+'</b>: Segons els experts, les fotos d\'aquesta observació podrien ser de mosquit de la febre groga (<i>Aedes aegypti</i>). \
          <p>Si es veuen molt clarament els seus trets taxonòmics, especialment la lira al cap i tòrax, serà "confirmat". Si no s\'aprecien alguns trets, serà "possible".</p> \
        </li> \
        <li><b>'+t('layer.other_species')+'</b>: Segons els experts, les fotos d\'aquesta observació podrien ser d\'altres espècies de mosquit.</li> \
        <li><b>'+t('layer.unidentifiede')+'</b>: Segons els experts, aquestes observacions i les seves fotos no permeten identificar cap espècie de mosquit.</li> \
        <li><b>'+t('layer.unclassified')+'</b>: Observacions amb foto que encara no han estat validades per experts.</li> \
        <li><b>'+t('layer.site')+'</b>: Observacions ciutadanes de possibles llocs de cria (embornals i altres) de mosquit tigre o de la febre groga. Inclou observacions que encara no han estat filtrades per experts.</li> \
        <li><b>Altres observacions</b>: Observacions que no corresponen a cap altra categoria però que podrien contenir informació d\'interès per a gestors.</li> \
        <li><b>'+t('layer.userfixes')+'</b>: Els quadres més foscos indiquen que hi ha més persones amb l\'app instal·lada o bé que hi ha usuaris que han estat molt de temps amb l\'app al seu mòbil.</li> \
      </ul> \
      <p>Per saber-ne més sobre els mètodes de classificació consultar <a href="http://www.mosquitoalert.com/mapa-y-resultados/mapa" target="blank">www.mosquitoalert.com/mapa-y-resultados/mapa</a></p> \
      <p>Més informació del projecte a <a href="http://www.mosquitoalert.com" target="blank">www.mosquitoalert.com</a></p>',

    'map.control_download': 'Descarregar dades',
    'map.download_btn': 'Descarregar dades',
    'map.text_description_download': '<p>La descàrrega es realitzarà a partir dels elements que es visualitzen al mapa. Comprova que tens actives les capes de la llegenda que desitges, els filtres temporals i el nivell de zoom.</p><p>Un cop definida la vista desitjada, fes clic al botó de descàrrega.</p>',
    'map.title_download': 'Descàrrega',

    'map.controlshare_view_description': 'Comparteix la vista privada d\'aquest mapa',
    'share.private_layer_warn': 'Atenció! La vista que vols compartir conté les següents dades privades:()Només els usuaris registrats tindran accés a aquesta vista.',
};
_.extend(trans.ca, add);
