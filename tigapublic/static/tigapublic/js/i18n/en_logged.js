var trans = trans || {};

add = {
    'layer.trash_layer': 'Other observations',

    'map.controlmoreinfo_desc_es': '<ul class="info_list"> \
        <li><b>'+t('layer.tiger')+'</b>: : According to experts, the pictures of this observation could be tiger mosquito (<i>Aedes albopictus</i>). \
          <p>If their taxonomic features can be clearly seen, especially the white stripe on head and thorax, it will be "confirmed". If some features cannot be observed, it will be "possible".</p> \
        </li> \
        <li><b>'+t('layer.zika')+'</b>: According to experts, the pictures of this observation could be yellow fever mosquito (<i>Aedes aegypti</i>). \
          <p>If their taxonomic features can be clearly seen, especially the lyre in the head and thorax, it will be "confirmed". If some features cannot be seen, it will be "possible".</p> \
        </li> \
        <li><b>'+t('layer.other_species')+'</b>: According to experts, the pictures of this observation may be of other species of mosquito.</li> \
        <li><b>'+t('layer.unidentified')+'</b>: According to experts, these observations and their photos do not identify any species of mosquito.</li> \
        <li><b>'+t('layer.unclassified')+'</b>: Observations with photo that have not yet been validated by experts.</li> \
        <li><b>'+t('layer.site')+'</b>: Citizens’ observations of possible breeding sites (storm drain or sewer) of tiger or yellow fever mosquitoes. It includes observations that have not yet been filtered by experts.</li> \
        <li><b>Other observations</b>: Observations that do not correspond to any other category but which may contain information of interest to managers.</li> \
        <li><b>'+t('layer.userfixes')+'</b>: Darker squares indicate places where there are more people with the app installed or that there are users who have had for long the app installed on their phones.</li> \
      </ul> \
      <p>To learn more about the methods of data classification check <a href="http://www.mosquitoalert.com/mapa-y-resultados/mapa" target="blank">www.mosquitoalert.com/mapa-y-resultados/mapa</a></p> \
      <p>More project information in <a href="http://www.mosquitoalert.com" target="blank">www.mosquitoalert.com</a></p>',

    'map.control_download': 'Download data',
    'map.download_btn': 'Download data',
    'map.text_description_download': '<p>Only data displayed in the current map view will be downloaded. Verify your current active layers, temporal filters and zoom.</p><p>Once verified, press the download button.</p>',
    'map.title_download': 'Download',

    'map.controlshare_view_description': 'Share this private map view',
    'share.private_layer_warn': 'Atention! The view you are about to share contains the following private data:()Only registered users will be able to visualize this view.',
};
_.extend(trans.en, add);
