var trans = trans || {};

add = {
    'layer.trash_layer': 'Altres observacions',
    'layer.unclassified': 'Per validar',

    'expertinfo.tiger_mosquito': ' Segons els experts, les fotos d\'aquesta observació podrien ser de mosquit tigre (<i>Aedes albopictus</i>). \
        <br/>Si es veuen molt clarament els seus trets taxonòmics, especialment la ratlla blanca al cap i tòrax, serà "confirmat". Si no s\'aprecien alguns trets, serà "possible".',
    'expertinfo.yellow_fever_mosquito':' Segons els experts, les fotos d\'aquesta observació podrien ser de mosquit de la febre groga (<i>Aedes aegypti</i>). \
      <br/>Si es veuen molt clarament els seus trets taxonòmics, especialment la lira al cap i tòrax, serà "confirmat". Si no s\'aprecien alguns trets, serà "possible".',
    'expertinfo.site': 'Observacions ciutadanes de possibles llocs de cria (embornals i altres) de mosquit tigre o de la febre groga. Inclou observacions que encara no han estat filtrades per experts.',
    'expertinfo.unclassified':'Observacions amb foto que encara no han estat validades per experts.',
    'expertinfo.trash_layer':'Observacions que no corresponen a cap altra categoria però que podrien contenir informació d\'interès per a gestors.',

    'map.control_download': 'Descarregar dades',
    'map.download_btn': 'Descarregar dades',
    'map.text_description_download': '<p>La descàrrega es realitzarà a partir dels elements que es visualitzen al mapa. Comprova que tens actives les capes de la llegenda que desitges, els filtres temporals i el nivell de zoom.</p><p>Un cop definida la vista desitjada, fes clic al botó de descàrrega.</p>',
    'map.title_download': 'Descàrrega',

    'map.controlshare_view_description': 'Comparteix la vista privada d\'aquest mapa',
    'share.private_layer_warn': 'Atenció! Les dades privades de la vista actual i algunes de les capes només seran visibles pels usuaris registrats.',
};
_.extend(trans.ca, add);
