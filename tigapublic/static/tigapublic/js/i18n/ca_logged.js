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

  'map.controlshare_view_description': 'Comparteix la vista privada d\'aquest mapa',
  'share.private_layer_warn': 'Atenció! Les dades privades de la vista actual i algunes de les capes només seran visibles pels usuaris registrats.',
  'map.notification_add':'Nova notificació',
  'notif.observations_none':'Cal seleccionar alguna observació',
  'notif.all_field_requiered':' Tots els camps són obligatoris',
  'notif.saved':'La notificació s\'ha enviat correctament',
  'notif.notification_cancel':'Cancel·la',

  //Descarregar
  'map.text_description_download': '<p>La descàrrega es realitzarà a partir dels elements que es visualitzen al mapa i només per a les dades relatives a les observacions ciutadanes. Comprova que tens actives les capes de la llegenda que desitges, els filtres temporals i el nivell de zoom.</p><p>Un cop definida la vista desitjada, fes clic al botó de descàrrega.</p>',
  //Notificacions
  'usernotification.not-predefined':'No predefinides',
  'all_notifications': 'Totes les notificacions',
  'check_notifications': 'Notificacions',
  'map.notification.notified': 'A',
  'map.notification.notifier': 'De',
  'map.notification.predefined.title': 'Si ho prefereixes pots fer servir una notificació predefinida:',
  'map.notification.preset0.body': '<p>Aquesta és la notificació predefinida número 1</p><p>Al cos del missatge posem el que convingui.</p>',
  'map.notification.preset0.title': 'Notificació predefinida 1',
  'map.notification.preset1.body': '<p>Aquesta és la notificació predefinida número 2</p><p>Al cos del missatge hi ha una mica més de text.</p>',
  'map.notification.preset1.title': 'Notificació predefinida 2',
  'map.notification.type.none': 'Tipus de notificació',
  'map.notification.type.private': 'Notificació privada',
  'map.notification.type.public': 'Notificació pública',
  'map.notification_add': 'Nova notificació',
  'map.notification_select_polygon_btn': 'Selecciona territori',
  'leaflet.draw.toolbar.cancel.title': 'Cancel·lar notificació',
  'map.control_notifications': 'Emetre notificació',
  'map.title_notification': 'Notificació',
  'notif.all_field_requiered': 'Tots els camps són obligatoris',
  'notif.notification_cancel': 'Cancel·lar',
  'notif.observations_none': 'No hi ha cap observació seleccionada',
  'notif.saved': 'Notificació enviada correctament',
  'notif.sendig_notifications': 'Les dades s\'estan enviant...',


  //Dibuix
  'map.text_description_notification': '<p>Fes clic a <span class="fa fa-pencil"></span> "Seleccionar territori" per seleccionar les observacions a les que vols enviar una notificació.</p><p>Pots tancar el polígon amb un doble clic sobre nou vèrtex, o amb un sol clic sobre el vèrtex inicial.<br/><br/>En finalitzar el polígon s\'indicarà el nombre d\'observacions afectades a la part superior d\'aquest panell i es mostrarà el formulari per crear la notificació.</p><p>En tancar el formulari de notificació caldrà tornar a començar la selecció del territori.</p>',

  //Select
    //Modal
  'map.users_found_text': 'Usuaris',
  'map.results_found_text': 'Observacions',

  'map.text_description_notification': '<p>Fes clic a <span class="fa fa-pencil"></span> "Seleccionar territori" per seleccionar les observacions a les que vols enviar una notificació.</p><p>Pots tancar el polígon amb un doble clic sobre nou vèrtex, o amb un sol clic sobre el vèrtex inicial.<br/><br/>Al finalitzar el polígon s\'indicarà el número d\'observacions afectades en la part superior del panell i es mostrarà el formulario para crear la notificació.</p><p>Al tancar el formulari de notificació serà necessari començar de nou amb la selecció del territori.</p>',

  //configuración de imbornales'stormdrain.label-versions': 'Número de versión',
  'layer.drainstorm': 'Embornals',
  'drainstorm.nowater': 'Sense aigua',
  'drainstorm.water': 'Amb aigua',
  'stormdrain.send': 'Enviar',
  'stormdrain.categories-helper1': 'Les categories seran avaluades per ordre de definició.',
  'stormdrain.categories-helper2': 'Només es representaran els embornals que compleixin totes les condicions.',
  'stormdrain.categories-helper3': 'Cada condició està formada per un atribut i un valor.',
  'stormdrain.categories-helper4': 'Els embornals ja assignats a una categoria no tornaran a ser avaluats.',
  'stormdrain.field-activity': 'Activitat',
  'stormdrain.field-date': 'Data',
  'stormdrain.field-sand': 'Sorra',
  'stormdrain.field-species1': 'Espècie A',
  'stormdrain.field-species2': 'Espècie B',
  'stormdrain.field-treatment': 'Tractament',
  'stormdrain.field-type': 'Tipus',
  'stormdrain.field-water': 'Aigua',
  'stormdrain.import-finished': 'La importació ha finalitzat correctament',
  'stormdrain.import-started': 'Important dades. Aquest procés pot tardar una estona.',
  'stormdrain.label-categories': 'Categories',
  'stormdrain.label-color': 'Color',
  'stormdrain.label-conditions': 'Condicions',
  'stormdrain.label-field': 'Atribut',
  'stormdrain.label-value': 'Valor',
  'stormdrain.label-versions': 'Versió',
  'stormdrain.main-title': 'Configuració de la visualització d\'embornals',
  'stormdrain.none-txt': 'Cap',
  'stormdrain.operator-<=': ' fins a',
  'stormdrain.operator-<>': ' diferent de',
  'stormdrain.operator-=': ' igual a',
  'stormdrain.operator->=': ' des de',
  'stormdrain.setup.submit.ok': 'S\'ha desat la nova configuració',
  'stormdrain.setup-later': 'Configurar embornals més tard',
  'stormdrain.setup-now': 'Continuar amb la configuració d\'embornals',
  'stormdrain.upload-button': 'Selecciona un fitxer',
  'stormdrain.get-template':'Descarregar plantilla',
  'stormdrain.upload-comment': 'Titol (max 30 caràcters)',
  'stormdrain.upload-error': 'S\'ha produït un error:',
  'stormdrain.upload-newversion': 'Versió número:',
  'stormdrain.upload-required': 'Tots els camps són obligatoris',
  'stormdrain.upload-title': 'Càrrega d\'embornals',
  'stormdrain.user-txt': 'Usuari',
  'stormdrain.value-0': 'No',
  'stormdrain.value-1': 'Si',
  'stormdrain.value-E': 'Embornal',
  'stormdrain.value-F': 'Font',
  'stormdrain.value-false': 'No',
  'stormdrain.value-R': 'Reixeta',
  'stormdrain.value-true': 'Sí',
  'stormdrain.value-null': 'Sense valor',
  'stormdrain.version-helper': 'Selecciona la versió que vols configurar',
  'stormdrain.version-txt': 'Versió',
  'stormdrain.water': 'Aigua',
  'stormdrain.example-title': 'Exemple de configuració de la visualització d\'embornals',
  'stormdrain.example-body-1': 'Es vol pintar, representar els embornals en dos categories, segons:',
  'stormdrain.example-body-2': 'Tenen aigua i han estat tractats. Representats de color verd',
  'stormdrain.example-body-3': 'Tenen aigua i no han estat tractats. Representats de color vermell',
  'stormdrain.example-body-4': 'En aquest cas, el que s’hauria de fer seria:',
  'stormdrain.example-body-5': 'img/stormdrain_example_1_ca.png',
  'stormdrain.example-body-6': 'El que <strong>NO</strong> funcionaria, seria configurar la visualització amb aquests paràmetres:',
  'stormdrain.example-body-7': 'img/stormdrain_example_2_ca.png',
  'stormdrain.example-body-8': 'Perquè no representaríem en aquest cas, dos tipus d’embornals (els que tenen aigua i estan tractats;  els que tenen aigua i no han estat tractats?), que estaríem representant en aquest cas?',
  'stormdrain.example-body-9': 'En color verd els embornals que tenen l’atribut «aigua» = «Sí». Independentment dels valors que tinguin els altres atributs (tractament, data, etc.).',
  'stormdrain.example-body-10': 'En color morat, els embornals que no han encaixat en la primera categoria, i que tenen l’atribut «Tractament» = «sí».',
  'stormdrain.example-body-11': 'En color blau, els embornals que no encaixen en cap de les dues categories anteriors, i que tenen la columna «Tractament» = «no».',
  'stormdrain.example-body-12': 'És a dir, cada color s’associa a una categoria. Cada categoria pot tenir una o més condicions. I cada condició fa referència a un «atribut» un operador (igual ,diferent de, etc.) i un «valor». ',
  'stormdrain.example-body-13': 'Perquè un embornal pertanyi a una categoria, cal que es compleixen totes les condicions de la categoria (operador lògic AND).',
  'stormdrain.example-body-14': 'També cal tenir present que quan un embornal «cau» dins d’una categoria, aquest embornal ja no s’avalua amb la resta de categories que venen a continuació. És a dir, un embornal que tingui la columna «aigua» = «si» i «tractament» = «si» es representarà de color verd perquè és la primera categoria de la quan en compleix totes les condicions (en aquest cas només n’hi ha una).',

  //configuración de la capa epidemiologia
  'layer.epidemiology': 'Epidemiologia',
  'epidemiology.upload-title': 'Carga de dades epidemiològiques',
  'epidemiology.get-template': 'Descarregar plantilla',
  'epidemiology.upload-button':'Selecciona un arxiu',
  'epidemiology.import-started': 'Important dades. Aquest procés pot tardar una estona',
  'epidemiology.import-finished': 'La importació ha finalitzat correctament',
  'epidemiology.setup-now': 'Continuar amb la configuració',
  'epidemiology.setup-later': 'Configurar més tard',
  'epi.tpl-title': 'Dades epidemiològiques',
  'epi.date_symptom':'Data primers simptomes',
  'epi.date_arribal': 'Data d\'arribada',
  'epi.date_notification': 'Data de notificació',
  'epi.date_nodate': 'Sense data',
  'epi.age': 'Edat',
  'epi.country':'País visitat',
  'epi.patient_state':'Estat',
  'epi.province':'Provincia',
  'epi.health_center':'Centre',
  'epi.year':'Any',
  'epidemiology.setup-title': 'Epidemiologia. Configuració de la visualització',
  'epidemiology.update': 'Actualitzar',
  'epidemiology.period': 'Per',
  'epidemiology.field-map': 'Tipus de mapa',
  'epidemiology.patient_state': 'Estat del pacient',
  'epidemiology.age_band': 'Franges d\'edat',
  'epidemiology.date_symptom': 'Data dels primers simptomes',
  'epidemiology.date_arribal': 'Data d\'arribada',
  'epidemiology.years': 'anys',
  'epidemiology.patient-filter': 'Estats dels pacients',
  'epidemiology.likely': 'Probable',
  'epidemiology.suspected': 'Sospitós',
  'epidemiology.confirmed': 'Confirmat',
  'epidemiology.group-confirmat': 'Confirmat',
  'epidemiology.confirmed-not-specified': 'Virus no especificat',
  'epidemiology.confirmed-den': 'Dengue',
  'epidemiology.confirmed-zk': 'Zika',
  'epidemiology.confirmed-yf': 'Febre groga',
  'epidemiology.confirmed-chk': 'Chikungunya',
  'epidemiology.confirmed-wnv': 'Virus de l\'oest del nil',

  'epidemiology.form.confirmed-not-specified': 'Confirmat. Virus no especificat',
  'epidemiology.form.confirmed-den': 'Confirmat. Dengue',
  'epidemiology.form.confirmed-zk': 'Confirmat. Zika',
  'epidemiology.form.confirmed-yf': 'Confirmat. Febre groga',
  'epidemiology.form.confirmed-chk': 'Confirmat. Chikungunya',
  'epidemiology.form.confirmed-wnv': 'Confirmat. Virus de l\'oest del nil',

  'epidemiology.undefined': 'Indefinit',
  'epidemiology.nocase': 'No hi ha cas',
  'epidemiology.all': 'Tots els estats',
  'epidemiology.filter-explanation':'Els filtres temporas del mapa també aplicaran a aquesta capa a partir del camp *data_arribada* o *data_notificacio* segons correspongui',
  'epidemiology.upload-explanation': 'ATENCIÓ!! Aquest procés d\'importació eliminarà totes les dades prèviament emmagatzemades de la capa d\'Epidemiologia',
  'epidemiology.empty-layer': 'En aquests moments no hi ha dades d\'epidemiologia',
  'epidemiology.upload-error': 'S\'ha produït un error durant el procés d\'importació',

  //model_selector
  'layer.models.virus': 'Tipo',
  'layer.models.den': 'Dengue',
  'layer.models.zika': 'Zika',
  'layer.models.yf': 'Febre groga',
  'layer.models.chk': 'Chikungunya',
  'layer.models.wnv': 'Virus de l\'oest del nil',

  'layer.predictionmodels.virus': 'Probabilitat malaltia',
  'layer.predictionmodels-virus.description': 'El mapa mostra estimacions de la probabilitat d\'alerta de mosquits tigre, que representa la probabilitat que un participant enviï un informe de mosquit tigre fiable durant un període de dues setmanes, controlant l\'esforç de mostreig (és a dir, que el model representa el fet que hi hagi més participants en algunes àrees que en altres).<p>Aquestes estimacions es mostren en una graella de 0,05 graus de latitud per 0,05 graus de longitud i es promitgen per mes. La probabilitat d\'alerta depèn principalment de la distribució de la població del mosquit tigre i de l\'esforç de mostreig collectiu, que varia segons la ubicació i el mes. La probabilitat d\'alerta s\'ha demostrat que és un bon predictor de la presència de mosquits tigre mesurat pels mètodes tradicionals de vigilància (ovitraps), tal com s\'explica a Nature Communications 8: 916 (2017), <a href="https://doi.org/10.1038/s41467-017-00914-9" target="_blank">https://doi.org/10.1038/s41467-017-00914-9</a>. Les estimacions s\'actualitzen setmanalment a mesura que apareixen noves dades.</p><p>Tingueu en compte que aquesta capa de probabilitat d\'alerta només es pot filtrar amb els selectors d\'any i mes que es mostren aquí (i no amb els filtres addicionals a continuació, que són per a altres capes).</p>',

  //sugbroups
  'group.tiger': 'Mosquit tigre',
  'group.zika': 'Mosquit febre groga',
  'group.japonicus': 'Aedes japonicus',
  'group.koreicus': 'Aedes koreicus',
  'group.culex': 'Culex pipiens',

  'header.motto': 'Mapa privat Mosquito Alert',
  'modal.firstvisit.title': 'Et donem la benvinguda al mapa privat de Mosquito Alert',
  'modal.firstvisit.content': '<p>Al mapa privat podràs consultar les dades de mosquits enviats per la ciutadania, mitjançant l\'app Mosquito Alert, i validats per professionals de l\'entomologia. També podràs consultar dades que encara no han estat validades, així com dades que no es fan públiques per contenir informació considerada sensible, però potencialment útil per al seguiment i control d\'aquestes espècies. L\'eina no sols et permet <b>visualitzar dades</b>, sinó també filtrar-les segons els teus interessos, elaborar <b>informes personalitzats</b> o fins i tot <b>descarregar-les</b>. A més, podràs <b>enviar notificacions</b> directament a la ciutadania a través de l\'app de Mosquito Alert, seleccionant observacions en el mapa.</p>' +
    '<ul>' +
      '<li><i class="fa fa-bars" aria-hidden="true"></i>  Obre les diferents capes de dades, filtra\'ls per data, etiqueta o municipi i consulta els models Mosquito Alert</li>' +
      '<li><i class="fa fa-info" aria-hidden="true"></i>  Consulta la informació del mapa</li>' +
      '<li><i class="fa fa-share-alt" aria-hidden="true"></i> Comparteix la vista del mapa</li>' +
      '<li><i class="fa fa-file-text-o" aria-hidden="true"></i> Elabora informes personalitzats</li>' +
      '<li><i class="fa fa-download" aria-hidden="true"></i> Descarrega les dades</li>' +
      '<li><i class="fa fa-bell" aria-hidden="true"></i> Envia notificacions a participants</li>' +
    '</ul>' +
    '<p>El mapa conté informació de 5 espècies de mosquits vectors de malalties: el <b>mosquit tigre</b> (<em>Aedes albopictus</em>), el <b>mosquit de la febre groga</b> (<em>Aedes aegypti</em>), el <b>mosquit del Japó</b> (<em>Aedes japonicus</em>), el <b>mosquit de Corea</b> (<em>Aedes koreicus</em>) i el <b>mosquit comú</b> (<em>Culex pipiens</em>). A més, pots visualitzar possibles <b>llocs de cria</b> d\'aquests insectes en la via pública. Aquesta informació es complementa amb <b>models de probabilitat</b>, elaborats a partir de les dades ciutadanes i amb <b>l\'esforç de mostreig</b> o <b>distribució de participants</b>. </p>' +
    '<p>Accedeix al <b>botó [?]</b> de cada capa o grup de capes, on trobaràs detalls de les diferents dades disponibles i el significat dels models.</p>' +
    '<p>Per a més informació, visita <a href="http://www.mosquitoalert.com">www.mosquitoalert.com</a> o contacta amb profs@mosquitoalert.com</p>',
  'observations.description': '<ul class="info_list">' +
    '<li class="tiger_mosquito"> <b>Mosquit tigre</b>: Segons els experts, les fotos d\'aquesta observació podrien ser de mosquit tigre (Aedes albopictus). Si es veuen molt clarament els seus trets taxonòmics, especialment la ratlla blanca al cap i tòrax, serà "confirmat". Si no s\'aprecien alguns trets, serà "possible".</li>' +
    '<li class="yellow_fever_mosquito"> <b>Mosquit febre groga</b>: Segons els experts, les fotos d\'aquesta observació podrien ser de mosquit de la febre groga (Aedes aegypti). Si es veuen molt clarament els seus trets taxonòmics, especialment la lira al cap i tòrax, serà "confirmat". Si no s\'aprecien alguns trets, serà "possible".</li>' +
    '<li class="aedes_japonicus"> <b>Aedes japonicus</b>: Segons els experts, les fotos d\'aquesta observació podrien ser d\'Aedes japonicus. Si es veuen molt clarament els seus trets taxonòmics, especialment les línies daurades sobre el tòrax i l\'última secció del tercer parell de potes uniformement negra, serà “confirmat”. Si no s\'aprecien alguns trets, serà “possible”.</li>' +
    '<li class="aedes_koreicus"> <b>Aedes koreicus</b>: Segons els experts, les fotos d\'aquesta observació podrien ser d\'Aedes koreicus. Si es veuen molt clarament els seus trets taxonòmics, especialment les línies daurades sobre el tòrax i l\'última secció del tercer parell de potes amb una banda blanca., serà “confirmat”. Si no s\'aprecien alguns trets, serà “possible”.</li>' +
    '<li class="culex"> <b>Mosquit comú</b>: Segons els experts, les fotos d\'aquesta observació podrien ser de mosquit comú (Culex pipiens). Serà “confirmat” quan s\'apreciï el color groguenc i grandària del mosquit, uns palps maxil·lars curts i el final de l\'abdomen arrodonit. Si no s\'aprecien alguns trets, serà “possible”.</li>' +
    '<li class="aedes_jap_kor"> <b>Aedes jap/kor</b>: Segons els experts, les fotos d\'aquesta observació podrien ser d\'Aedes japonicus o Aedes koreicus. Els experts no poden determinar amb seguretat de quin de les dues espècies es tracta, al no poder apreciar a la foto el caràcter que les distingeix.</li>' +
    '<li class="aedes_albo_cret"> <b>Aedes albo/cret</b>: Segons els experts, les fotos d\'aquesta observació podrien ser d\'Aedes albopictus o Aedes cretinus. Els experts no poden determinar amb seguretat de quin de les dues espècies es tracta, al no poder apreciar a la foto el caràcter que les distingeix.</li>' +
    '<li class="other_species"> <b>Altres espècies</b>: Segons els experts, les fotos d\'aquesta observació podrien ser d\'altres espècies de mosquit.</li>' +
    '<li class="unidentified"> <b>No identificable</b>: Segons els experts, aquestes observacions i les seves fotos no permeten identificar cap espècie de mosquit.</li>' +
    '<li class="unclassified private"><b>Per validar</b>: Observacions amb foto que encara no han estat validades per experts.</li>' +
    '<li class="site"> <b>Llocs de cria</b>: Observacions ciutadanes de possibles llocs de cria (imbornals) de qualsevol de les 5 espècies estudiades per Mosquito Alert.</li>' +
    '<li class="trash_layer private"> <b>Altres observacions</b>: Observacions que no corresponen a cap altra categoria però que podrien contenir informació d\'interès per als gestors.</li>' +
    '</ul>',
  'models.description': '<ul class="info_list">' +
    '<li><b>Probabilitat Mosquit Alert</b>: Probabilitat de trobada amb mosquit tigre (Aedes albopictus) o mosquit del Japó (Aedes japonicus) basada en les observacions rebudes per Mosquito Alert. Més detalls en la capa del mapa, botó [?]. </li>' +
    '<li><b>Probabilitat picades</b>: Probabilitat de rebre una picada de mosquit basada en les notificacions rebudes en Mosquito Alert. Més detalls en la capa del mapa, botó [?].</li>' +
    '<li><b>Probabilitat malaltia</b>: Models de predicció de risc de malalties arbovirals per als municipis de Catalunya. Més detalls en la capa del mapa, botó [?].</li>' +
    '</ul>',
  'layer.predictionmodels.viruscontent' : 'Models de predicció de risc de malalties arbovirals per als municipis de Catalunya. Les probabilitats s\'estimen considerant tant informació de casos importats de les malalties com de variables climàtiques, abundància de mosquits i factors socioeconòmics. Els models s\'han desenvolupat dins del projecte Plataforma Integral per al Control d’Arbovirosis a Catalunya (PICAT) coordinat pel Vall d\'Hebron Institut de Recerca (VHIR) en col·laboració amb l\'Agència de Salut Pública de Catalunya (ASPCAT), ISGlobal i Mosquito Alert.',
};
_.extend(trans.ca, add);
