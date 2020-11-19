var trans = trans || {};

add = {
    'layer.trash_layer': 'Other observations',
    'layer.unclassified': 'To validate',

    'expertinfo.tiger_mosquito': ' According to experts, the pictures of this observation could be tiger mosquito (<i>Aedes albopictus</i>). \
      <br/>If their taxonomic features can be clearly seen, especially the white stripe on head and thorax, it will be "confirmed". If some features cannot be observed, it will be "possible".',
    'expertinfo.yellow_fever_mosquito':' According to experts, the pictures of this observation could be yellow fever mosquito (<i>Aedes aegypti</i>). \
      <br/>If their taxonomic features can be clearly seen, especially the lyre in the head and thorax, it will be "confirmed". If some features cannot be seen, it will be "possible".',
    'expertinfo.site': 'Citizens’ observations of possible breeding sites (storm drain or sewer) of tiger or yellow fever mosquitoes. It includes observations that have not yet been filtered by experts.',
    'expertinfo.unclassified':'Observations with photo that have not yet been validated by experts.',
    'expertinfo.trash_layer':'Observations that do not correspond to any other category but which may contain information of interest to managers.',

    'map.controlshare_view_description': 'Share this private map view',
    'share.private_layer_warn': 'Attention! The private data and some of its layers of the current view will only be visible to registered users.',

    //download
    'map.text_description_download': '<p>Only observation citizen data displayed in the current map view will be downloaded. Verify your current active layers, temporal filters and zoom.</p><p>Once verified, press the download button.</p>',

    //Notification
  'usernotification.not-predefined':'Not predefined',
  'check_notifications': 'Notifications',
  'map.control_notifications': 'Issue notification',
  'map.notification.notified': 'To',
  'map.notification.notifier': 'From',
  'map.notification.predefined.title': 'You can use a predefined notification if you want:',
  'map.notification.preset0.body': '<p>This is predefined notification number 1</p><p>Fill the message body as needed.</p>',
  'map.notification.preset0.title': 'Predefined notification 1',
  'map.notification.preset1.body': '<p>This is predefined notification number 2</p><p>There\'s a little bit more text in the message body.</p>',
  'map.notification.preset1.title': 'Predefined notification 2',
  'map.notification.type.none': 'Notification type',
  'map.notification.type.private': 'Private notification',
  'map.notification.type.public': 'Public notification',
  'map.notification_add': 'New notification',
  'map.notification_select_polygon_btn': 'Select territory',
  'map.text_description_notification': '<p>Click <span class="fa fa-pencil"></span> "Select territory" to select the observations which will be sent a notification.</p><p>You can close the polygon double clicking a new vertex, or single clicking an existing vertex (...)',
  'notif.saved': 'Notification successfully sent',
  'notif.notification_cancel': 'Cancel',
  'notif.observations_none': 'No observations selected',
  'notif.sendig_notifications': 'Data is being sent...',

  //modal
  'map.users_found_text': 'Users',
  'info.notifications': 'Notifications',
  'notif.all_field_requiered': 'All fields are required',
  'map.results_found_text': 'Observations',
  'map.title_notification': 'Notification',

  //Draw
  'map.text_description_notification': '<p>Click <span class="fa fa-pencil"></span> "Select territory" to select the observations which will be sent a notification.</p><p>You can close the polygon double clicking a new vertex, or single clicking the starting vertex.<br/><br/>When finishing the polygon, the number of affected observations will be shown on top of this panel and the notification creation form will pop up.</p><p>When the notification form is closed the territory selection must start again.</p>',
  'leaflet.draw.toolbar.cancel.title': 'Cancel notification',

  //Storm Drain
  'stormdrain.send': 'Send',
  'layer.drainstorm': 'Storm drains',
  'drainstorm.nowater': 'Without water',
  'drainstorm.water': 'With water',
  'stormdrain.categories-helper1':'Categories will be evaluated by order of definition.',
  'stormdrain.categories-helper2':'A storm drain will be assigned to a category only if it meets all the specified conditions.',
  'stormdrain.categories-helper3':'Every condition is made out of an attribute and a value.',
  'stormdrain.categories-helper4':'Storm drains which are already assigned to a category will not be evaluated again.',
  'stormdrain.field-activity': 'Activity',
  'stormdrain.field-date': 'Date',
  'stormdrain.field-sand': 'Sand',
  'stormdrain.field-species1': 'Species A',
  'stormdrain.field-species2': 'Species B',
  'stormdrain.field-treatment': 'Treatment',
  'stormdrain.field-type': 'Type',
  'stormdrain.field-water': 'Water',
  'stormdrain.import-finished': 'Import completed successfully',
  'stormdrain.import-started': 'Importing data. This could take a while.',
  'stormdrain.label-categories': 'Categories',
  'stormdrain.label-color': 'Color',
  'stormdrain.label-conditions': 'Conditions',
  'stormdrain.label-field': 'Field',
  'stormdrain.label-value': 'Value',
  'stormdrain.label-versions': 'Version',
  'stormdrain.main-title': 'Storm drain visualization setup',
  'stormdrain.none-txt': 'None',
  'stormdrain.operator-<=': ' up to',
  'stormdrain.operator-<>': ' not equal to',
  'stormdrain.operator-=': ' equal to',
  'stormdrain.operator->=': ' from',
  'stormdrain.setup.submit.ok': 'New configuration has been saved',
  'stormdrain.setup-later': 'Configure storm drains later',
  'stormdrain.setup-now': 'Continue with storm drain configuration',
  'stormdrain.upload-button': 'Select file',
  'stormdrain.get-template':'Download template',
  'stormdrain.upload-comment': 'Title (30 characters max)',
  'stormdrain.upload-error': 'There has been an error:',
  'stormdrain.upload-newversion': 'Version number:',
  'stormdrain.upload-required': 'All fields are required',
  'stormdrain.upload-title': 'Storm drain upload',
  'stormdrain.user-txt': 'User',
  'stormdrain.value-0': 'No',
  'stormdrain.value-1': 'Yes',
  'stormdrain.value-E': 'Storm drain',
  'stormdrain.value-F': 'Fountain',
  'stormdrain.value-false': 'No',
  'stormdrain.value-R': 'Grating',
  'stormdrain.value-true': 'Yes',
  'stormdrain.value-null': 'No value',
  'stormdrain.version-helper': 'Select version to setup',
  'stormdrain.version-txt': 'Version',
  'stormdrain.water': 'Water',
  'stormdrain.example-title': 'Storm drain configuration example',
  'stormdrain.example-body-1': 'We want to represent and color-code storm drains in the following two categories:',
  'stormdrain.example-body-2': 'With water and treated. Green-coloured',
  'stormdrain.example-body-3': 'With water and non-treated. Red-coloured',
  'stormdrain.example-body-4': 'We would need to do this:',
  'stormdrain.example-body-5': 'img/stormdrain_example_1_en.png',
  'stormdrain.example-body-6': 'If we configured the visualization using the following settings, this would <strong>NOT</strong> work: ',
  'stormdrain.example-body-7': 'img/stormdrain_example_2_en.png',
  'stormdrain.example-body-8': 'Why in this case we would not see two types of storm drains (with water and treated; and with water and non-treated)?, What would we be seeing?',
  'stormdrain.example-body-9': 'Green-coloured storm drains with the attribute «water» = «Yes». Independently of the values of other attributes (treatment, date, etc.).',
  'stormdrain.example-body-10': 'Purple-coloured, storm drains that don’t fit with the first category and have the attribute «Treatment» = «Yes».',
  'stormdrain.example-body-11': 'Blue-coloured, storm drains that don’t fit neither the two categories and have the column «Treatment» = «No».',
  'stormdrain.example-body-12': 'Each colour is associated with a category. Each category can have one or more conditions. Each condition refers to an attribute, an operator (equal to, not equal to, etc.) and a «value».',
  'stormdrain.example-body-13': 'Storm drains must have all the conditions of the categories in order to fit in each one (logical operator AND).',
  'stormdrain.example-body-14': 'When a storm drain fits in one category, it is not evaluated in the other categories. For example, when one storm drain has the column «water»= «Yes» and «treatment» = «Yes» is will be represented in Green, because it’s the first category that matches all the conditions (in this case there is only one).',

  //configuración de la capa epidemiologia
  'layer.epidemiology': 'Epidemiology',
  'epidemiology.upload-title': 'Epidemiology upload',
  'epidemiology.get-template': 'Epidemiology template',
  'epidemiology.upload-button': 'Select file',
  'epidemiology.import-started': 'Importing data. This could take a while.',
  'epidemiology.import-finished': 'Import completed successfully',
  'epidemiology.setup-now': 'Continue with data configuration',
  'epidemiology.setup-later': 'Configure later',
  'epi.tpl-title':'Epidemiology data',
  'epi.date_symptom': 'Date first symptoms',
  'epi.date_arribal': 'Arribal date',
  'epi.date_notification': 'Notification date',
  'epi.date_nodate': 'No date',
  'epi.age': 'Age',
  'epi.country': 'Country',
  'epi.patient_state':'State',
  'epi.province':'Province',
  'epi.health_center':'Center',
  'epi.year':'Year',
  'epidemiology.setup-title': 'Epidemiology. View setup',
  'epidemiology.update': 'Update',
  'epidemiology.period': 'By',
  'epidemiology.field-map': 'Map type',
  'epidemiology.patient_state': 'Patient state',
  'epidemiology.age_band': 'Age ranges',
  'epidemiology.date_symptom': 'Sympthoms date',
  'epidemiology.date_arribal': 'Arribal date',
  'epidemiology.years': 'years',
  'epidemiology.patient-filter': 'Patient states',
  'epidemiology.likely': 'Likely',
  'epidemiology.suspected': 'Suspected',
  'epidemiology.confirmed': 'Confirmed',
  'epidemiology.group-confirmat': 'Confirmed',
  'epidemiology.confirmed-not-specified': 'Virus not specified',
  'epidemiology.confirmed-den': 'Dengue',
  'epidemiology.confirmed-zk': 'Zika',
  'epidemiology.confirmed-yf': 'Yellow fever',
  'epidemiology.confirmed-chk': 'Chikungunya',
  'epidemiology.confirmed-wnv': 'West nile virus',

  'epidemiology.form.confirmed-not-specified': 'Confirmed. Virus not specified',
  'epidemiology.form.confirmed-den': 'Confirmed. Dengue',
  'epidemiology.form.confirmed-zk': 'Confirmed. Zika',
  'epidemiology.form.confirmed-yf': 'Confirmed. Yellow fever',
  'epidemiology.form.confirmed-chk': 'Confirmed. Chikungunya',
  'epidemiology.form.confirmed-wnv': 'Confirmed. West nile virus',

  'epidemiology.undefined': 'Undefined',
  'epidemiology.nocase': 'No case',
  'epidemiology.all': 'All states',
  'epidemiology.filter-explanation':'If a date filter is applied to the map, it will also be applied to this layer on *date_arribal* or *date_notification* field',
  'epidemiology.upload-explanation': 'WARNING!! The upload proces will delete all previouly stored data for the epidemiology layer',
  'epidemiology.empty-layer': 'There is no epidemiology data available at the moment',
  'epidemiology.upload-error': 'An error occurred while importing data',

  //model_selector
  'layer.models.virus': 'Type',
  'layer.models.den': 'Dengue',
  'layer.models.zika': 'Zika',
  'layer.models.yf': 'Yellow fever',
  'layer.models.chk': 'Chikungunya',
  'layer.models.wnv': 'West nile virus',
  'layer.predictionmodels.virus': 'Virus probability',
  'layer.predictionmodels-virus.description': 'The map shows estimates of the tiger mosquito alert probability, which represents the probability of a participant sending a reliable tiger mosquito report during any given two-week period, controlling for sampling effort (meaning that the model accounts for the fact that there are more participants in some areas than others).<p>These estimates are shown on a grid of 0.05 degrees latitude by 0.05 degrees longitude and are averaged by month. The alert probability mainly depends on the tiger mosquito’s population distribution, and this varies by location as well as month. The alert probability has been shown to be a good predictor of tiger mosquito presence measured by traditional surveillance methods (ovitraps), as explained in Nature Communications 8:916 (2017), <a href="https://doi.org/10.1038/s41467-017-00914-9" target="_blank">https://doi.org/10.1038/s41467-017-00914-9</a>. The estimates are updated weekly as new data comes in.</p><p>Note that this alert probability layer can be filtered only with the year and month selectors shown here (and not with the additional filters below, which are for other layers)</p>',

  //sugbroups
  'group.tiger': 'Tiger mosquito',
  'group.zika': 'Yellow fever mosquito',
  'group.japonicus': 'Aedes japonicus',
  'group.koreicus': 'Aedes koreicus',
  'group.culex': 'Culex pipiens',
  'group.mix': 'Aedes jap/kor',

  'header.motto': 'Mosquito Alert Private Map',

  'modal.firstvisit.title': 'Welcome to Mosquito Alert Private Map',
  'modal.firstvisit.content': '<p>On the private map you can check the mosquito data sent by citizens, through the Mosquito Alert app, and validated by entomologists. You can also explore data that have not yet been validated by experts, and data that is not public because it contains sensitive information. Not public data or not yet validated data might be relevant for surveillance and control. The tool allows you to <b>view, filter and download data</b>, according to your interests and prepare <b>personalized reports</b>. You can also <b>send notifications</b> to citizens through the Mosquito Alert app, selecting observations on the map.</p>' +
    '<ul>' +
      '<li><i class="fa fa-bars" aria-hidden="true"></i> Open the different data layers, filter them by date, hashtag or municipality and consult the Mosquito Alert models</li>' +
      '<li><i class="fa fa-info" aria-hidden="true"></i> Check the map information</li>' +
      '<li><i class="fa fa-share-alt" aria-hidden="true"></i> Share the map view</li>' +
      '<li><i class="fa fa-file-text-o" aria-hidden="true"></i> Create custom reports</li>' +
      '<li><i class="fa fa-download" aria-hidden="true"></i> Download the data</li>' +
      '<li><i class="fa fa-bell" aria-hidden="true"></i> Issue notifications to participants</li>' +
    '</ul>' +
    '<p>The map contains information on 5 species of disease-vector mosquitoes: the <b>tiger mosquito</b> (<em>Aedes albopictus</em>), the <b>yellow fever mosquito</b> (<em>Aedes aegypti</em>), the <b>Asian bush mosquito</b> (<em>Aedes japonicus</em>), <em>Aedes koreicus</em> and the <b>common house mosquito</b> (<em>Culex pipiens</em>). In addition, you can visualize possible <b>breeding places</b> for these insects on public spaces. This information is complemented with <b>probability models</b>, elaborated from the citizen data and considering the <b>sampling effort</b> or <b>distribution of participants</b>.</p>' +
    '<p>Click the <b>[?] Button</b> for each layer or group of layers, where you will find details of the different data available and the meaning of the models.</p>'  +
    '<p>For more information, visit <a href="http://www.mosquitoalert.com">www.mosquitoalert.com</a> or contact profs@mosquitoalert.com.</p>',
  'observations.description': '<ul class="info_list">' +
    '<li class="tiger_mosquito"> <b>Tiger mosquito</b>: According to experts, the pictures of this observation could be tiger mosquito (Aedes albopictus). If its taxonomic features are seen very clearly, especially the white stripe on the head and thorax, it will be "confirmed". If some traits are not appreciated, it will be "possible".</li>' +
    '<li class="yellow_fever_mosquito"> <b>Yellow fever mosquito</b>: According to experts, the pictures of this observation could be yellow fever mosquito (Aedes aegypti). If its taxonomic features, especially the lyre on the head and thorax, are very clearly seen, it will be “confirmed”. If some traits are not appreciated, it will be "possible".</li>' +
    '<li class="aedes_japonicus"> <b>Aedes japonicus</b>: According to experts, the pictures of this observation could be Aedes japonicus. If its taxonomic features are seen very clearly, especially the golden strips on the thorax and the last section of the third pair of legs is uniformly black, it will be "confirmed". If some traits are not appreciated, it will be "possible".</li>' +
    '<li class="aedes_koreicus"> <b>Aedes koreicus</b>: According to experts, the pictures of this observation could be Aedes koreicus. If its taxonomic features are seen very clearly, especially the golden stripes on the thorax and the last section of the third pair of legs with a white band, it will be "confirmed". If some traits are not appreciated, it will be "possible".</li>' +
    '<li class="culex"> <b>Culex pipiens</b>: According to experts, the pictures of this observation could be Culex pipiens. It will be “confirmed” when the yellowish color and size of the mosquito, short maxillary palps and the rounded end of the abdomen are appreciated. If some traits are not appreciated, it will be "possible".</li>' +
    '<li class="aedes_jap_kor"> <b>Aedes jap/kor</b>: According to experts, the pictures of this observation could be Aedes japonicus or Aedes koreicus. Experts cannot determine with certainty which of the two species it is, as they cannot appreciate the character that distinguishes them in the photo.</li>' +
    '<li class="aedes_albo_cret"> <b>Aedes albo/cret</b>: According to experts, the pictures of this observation could be Aedes albopictusor Aedes cretinus. Experts cannot determine with certainty which of the two species it is, as they cannot appreciate the character that distinguishes them in the photo.</li>' +
    '<li class="other_species"> <b>Other species</b>: According to experts, the pictures of this observation may be of other species of mosquito.</li>' +
    '<li class="unidentified"> <b>Unidentifiable</b>: According to experts, these observations and their photos do not identify any species of mosquito.</li>' +
    '<li class="unclassified private"><b>Pending validation</b>: Observations with picture which still haven\'t been validated by experts.</li>' +
    '<li class="site"> <b>Breeding sites</b>: Citizen’ observations of possible breeding sites (storm drainers and sewers) of the five species studied by Mosquito Alert.</li>' +
    '<li class="trash_layer private"> <b>Other observations</b>: Observations not belonging to any other category but which could contain interesting info for the private map users.</li>' +
    '</ul>',
  'models.description': '<ul class="info_list">' +
    '<li><b>Mosquito Alert Probability</b>: Probability of encountering a tiger mosquito (Aedes albopictus) or an Asian bush mosquito (Aedes japonicus) based on the observations received in Mosquito Alert. More details on the map layer, [?] button.</li>' +
    '<li><b>Bites probability</b>: Probability of receiving a mosquito bite based on notifications received in Mosquito Alert. More details on the map layer, [?] button.</li>' +
    '<li><b>Disease probability</b>: Prediction models for arboviral diseases in Catalan municipalities. More details on the map layer, [?] button.</li>' +
    '</ul>',
  'layer.predictionmodels.viruscontent' : 'Risk prediction models for arboviral diseases in Catalan municipalities. Probabilities are estimated considering information about imported cases as well as climate variables, mosquito abundance and socio economical factors. The models have been developed on the project Plataforma Integral per al Control d’Arbovirosis a Catalunya (PICAT), coordinated by Vall d’Hebron Institut de Recerca (VHIR) in collaboration with the Agencia de Salud Pública de Cataluña (ASPCAT), ISGlobal and Mosquito Alert.',
};
_.extend(trans.en, add);
