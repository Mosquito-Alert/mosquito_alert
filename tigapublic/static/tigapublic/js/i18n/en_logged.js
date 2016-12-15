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

    'map.control_download': 'Download data',
    'map.download_btn': 'Download data',
    'map.text_description_download': '<p>Only data displayed in the current map view will be downloaded. Verify your current active layers, temporal filters and zoom.</p><p>Once verified, press the download button.</p>',
    'map.title_download': 'Download',

    'map.controlshare_view_description': 'Share this private map view',
    'share.private_layer_warn': 'Attention! The private data and some of its layers of the current view will only be visible to registered users.',
};
_.extend(trans.en, add);
