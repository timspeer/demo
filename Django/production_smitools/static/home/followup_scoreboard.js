$(document).ready( function () {
    $('#myTable2').DataTable({
      searching: false,
      paging: false,
      info: false,
    });
  });

$(document).ready( function () {
    var total = 0
    var beg_date = new Date("01/01/2019")
    var date = new Date();
    date.setDate(date.getDate());
    var day = date.getDate();
    var month = date.getMonth() + 1;
    var year = date.getFullYear();
    if (month < 10) month = "0" + month;
    if (day < 10) day = "0" + day;
    var end_date = year + "-" + month + "-" + day;
    end_date = new Date(end_date)
    var clients = {
        "AACE" : AACE,
        "ANSA" : ANSA,
        "BELL" : BELL,
        "BLDR" : BLDR,
        "BSKY" : BSKY,
        "GVAA" : GVAA,
        "LONG" : LONG,
        "MAPP" : MAPP,
        "MTRX" : MTRX,
        "NMPS" : NMPS,
        "NRAC" : NRAC,
        "OLYY" : OLYY,
        "PACE" : PACE,
        "PCFC" : PCFC,
        "RENO" : RENO,
        "RETA" : RETA,
        "SCAA" : SCAA,
        "SOSA" : SEAT,
        "SPAN" : SOSA,
        "STPT" : STPT,
        "VALL" : VALL
    };
    for (var key in clients) {
    var value = clients[key]
    var arr = value.replace("[", "").replace("]", "")
    arr = arr.split(",");
    for (var i = 0; i < arr.length; i++){
        arr[i] = new Date(arr[i])
    };
    for (var i = 0; i < arr.length; i++){
        arr = arr.filter(function(item) {
        return item < end_date;
    })};
    for (var i = 0; i < arr.length; i++){
        arr = arr.filter(function(item) {
        return item > beg_date;
    })};
    key_val = "#" + key
    $(key_val).text((arr.length));
    total = total + arr.length;
    };
    $("h3").text("Current Total = " + total)
    $("#beg_date").val(beg_date.toISOString().split('T')[0]);
    $("#end_date").val(end_date.toISOString().split('T')[0]);
    });
  
  function followup() {
    var total = 0
    var beg_date = new Date($("#beg_date").val())
    var end_date = new Date($("#end_date").val())
    var clients = {
        "AACE" : AACE,
        "ANSA" : ANSA,
        "BELL" : BELL,
        "BLDR" : BLDR,
        "BSKY" : BSKY,
        "GVAA" : GVAA,
        "LONG" : LONG,
        "MAPP" : MAPP,
        "MTRX" : MTRX,
        "NMPS" : NMPS,
        "NRAC" : NRAC,
        "OLYY" : OLYY,
        "PACE" : PACE,
        "PCFC" : PCFC,
        "RENO" : RENO,
        "RETA" : RETA,
        "SCAA" : SCAA,
        "SOSA" : SEAT,
        "SPAN" : SOSA,
        "STPT" : STPT,
        "VALL" : VALL
    };
    for (var key in clients) {
      var value = clients[key]
      var arr = value.replace("[", "").replace("]", "")
      arr = arr.split(",");
      for (var i = 0; i < arr.length; i++){
        arr[i] = new Date(arr[i])
      };
      for (var i = 0; i < arr.length; i++){
        arr = arr.filter(function(item) {
          return item < end_date;
      })};
      for (var i = 0; i < arr.length; i++){
        arr = arr.filter(function(item) {
          return item > beg_date;
      })};
      key_val = "#" + key
      $(key_val).text((arr.length));
      total = total + arr.length;
    };
    $("h3").text("Current Total = " + total)
  };