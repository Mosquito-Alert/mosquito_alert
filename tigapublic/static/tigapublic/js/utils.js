accentsTidy = function(s){
    var r = s.toLowerCase();
    non_asciis = {'a': '[àáâãäå]', 'ae': 'æ', 'c': 'ç', 'e': '[èéêë]', 'i': '[ìíîï]', 'n': 'ñ', 'o': '[òóôõö]', 'oe': 'œ', 'u': '[ùúûűü]', 'y': '[ýÿ]'};
    for (i in non_asciis) { r = r.replace(new RegExp(non_asciis[i], 'g'), i); }
    return r;
};

function saveCSV(data) {
  var table = '';
  data.forEach(function(row) {
    table += row + '\r\n';
  });
  var blob = new Blob(["\ufeff", table], {
    type: 'text/csv'
  });
  saveAs(blob, "chart_data.csv");
}

function saveTrapData(data, metadata) {
  var zip = new JSZip();
  var table = '';
  var data_without_nulls = [];
  var labels_without_nulls = [];
  data.forEach(function(row, idx) {
    if (idx !== 0) {
      var serie = [];
      row.forEach(function(value, idx2) {
        if (value !== null) {
          if (idx === 1) {
            labels_without_nulls.push(data[0][idx2]);
          }
          serie.push(value);
        }
      });
      data_without_nulls.push(serie);
    }
  });
  data = [labels_without_nulls].concat(data_without_nulls);
  console.log(data);
  data.forEach(function(row) {
    table += row + '\r\n';
  });
  var blob = new Blob(["\ufeff", table], {
    type: 'text/csv'
  });
  zip.file(MOSQUITO.config.TRAPS_DOWNLOAD_FILE_NAME + '.csv', blob);
  zip.file('metadata.txt', metadata);
  zip.generateAsync({type:"blob"}).then(function(content) {
    // see FileSaver.js
    saveAs(content, MOSQUITO.config.TRAPS_DOWNLOAD_FILE_NAME + ".zip");
});
}
