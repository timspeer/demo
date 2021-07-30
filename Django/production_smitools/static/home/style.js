function show_in_phi() {
  var re = /http:\/\/smitools.supmed.local\/reconcile\/[a-z]{4}\/$/
  if (window.location.href.match(re)) {
    var url = document.location.href+"in_phi/";
    document.location = url;
  } else {
    var url = document.location.href;
    url = url.replace("in_phi/", '')
    document.location = url;
  }
}

function followup_accordion(ele) {
  var acc = document.getElementsByClassName("subtable "+ele);
  for (var i=0;i< acc.length;i++) {
    if (acc[i].style.display === "none") {
      acc[i].style.display = "block"
    } else {
      acc[i].style.display = "none"
    }
  }
}

function accordion(ele) {
  var acc = document.getElementsByClassName(ele);
  for (var i=0;i< acc.length;i++) {
    if (acc[i].style.display === "none") {
      acc[i].style.display = "block"
    } else {
      acc[i].style.display = "none"
    }
  }
}


$(document).ready( function () {
  var re = /http:\/\/smitools.supmed.local\/[a-z]+_reconcile\/in_phi\//
  if (window.location.href.match(re)) {
    var id = document.getElementById('phi');
    id.style.backgroundColor = "rgb(152, 152, 152)";
  };
});

function downloadCSV(csv, filename) {
  var csvFile;
  var downloadLink;
  csvFile = new Blob([csv], {type: "text/csv"});
  downloadLink = document.createElement("a");
  downloadLink.download = filename;
  downloadLink.href = window.URL.createObjectURL(csvFile);
  downloadLink.style.display = "none";
  document.body.appendChild(downloadLink);
  downloadLink.click();
}

function fnExcelReport(filename) {
  var csv = [];
  var rows = document.querySelectorAll("table tr");
  for (var i = 0; i < rows.length; i++) {
      var row = [], cols = rows[i].querySelectorAll("td, th");
      for (var j = 0; j < cols.length; j++) 
          row.push(cols[j].textContent.trim());
      csv.push(row.join(","));        
  }
  downloadCSV(csv.join("\n"), filename);
}


$(document).ready( function () {
  $('#myTable').DataTable({
    "order": [[ 2, 'asc']],
    paging: false,
    "dom": '<"top"i><"top"f>',
    "fixedHeader": true,
    "language": {
      "info": "Current Total = _TOTAL_",
      "infoFiltered": "(filtered from _MAX_ total records)"
    },
    "fnDrawCallback": function() {
      var table = document.getElementById("myTable");
      var tr = table.getElementsByTagName("tr");
      var count = -1
      for (var i = 0; i < tr.length; i++) {
        if (tr[i].style.display == "") {
          count = count + 1
        };
      }
      $('#myTable_info').html('Current Total = '+(count));
    }
  });
});

function custom_alert(msg, duration) {
  var el = document.createElement("dialog");
  Object.assign(el, {
    id: "msgBox",
    innerHTML: msg,
  })
  var body = document.getElementsByTagName("body")[0]
  body.insertBefore(el, body.childNodes[1])
  document.getElementById("msgBox").show()
  setTimeout(function() {
    document.getElementById("msgBox").remove()
  }, duration);
}

$(function() {
  $('.copy').on('click', function() {
    var value = this.value
    var textArea = document.createElement("textarea");
    textArea.value = value;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand("copy")
    textArea.remove();
    custom_alert("Link has been copied", "1000");
  });
});

function range() {
  var beg_date = document.getElementById("beg_date");
  var end_date = document.getElementById("end_date");
  beg_date = new Date(beg_date.value)
  end_date = new Date(end_date.value)
  var table = document.getElementById("myTable");
  var tr = table.getElementsByTagName("tr");
  var count = 0
  for (var i = 0; i < tr.length; i++) {
    var td = tr[i].getElementsByTagName("td")[2];
    if (td) {
      td = td.textContent.slice(0, 11).trim();
      var txtValue = new Date(td);
      if (txtValue >= beg_date && txtValue <= end_date) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
      if (document.getElementById("end_date").value == "") {
        tr[i].style.display = "";
      } 
      if (tr[i].style.display == "") {
        count = count + 1
      };
    } 
  }
  $('#wrapper').height($('#myTable').height())
  $('#myTable_info').html('Current Total = '+(count));
}

function init_search() {
  var date = new Date();
  date.setDate(date.getDate() - 60);
  var day = date.getDate();
  var month = date.getMonth() + 1;
  var year = date.getFullYear();
  if (month < 10) month = "0" + month;
  if (day < 10) day = "0" + day;
  var today = year + "-" + month + "-" + day;
  document.getElementById("beg_date").value = today;
  var date2 = new Date();
  date2.setDate(date2.getDate() - 9);
  var day2 = date2.getDate();
  var month2 = date2.getMonth() + 1;
  var year2 = date2.getFullYear();
  if (month2 < 10) month2 = "0" + month2;
  if (day2 < 10) day2 = "0" + day2;
  var today2 = year2 + "-" + month2 + "-" + day2;
  document.getElementById("end_date").value = today2;
  var table = document.getElementById("myTable");
  var tr = table.getElementsByTagName("tr");
  var count = 0
  for (var i = 0; i < tr.length; i++) {
    var td = tr[i].getElementsByTagName("td")[2];
    if (td) {
      var txtValue = td.textContent || td.innerText;
      if (txtValue >= today && txtValue <= today2) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
      if (tr[i].style.display == "") {
        count = count + 1
      };
    }       
  }
  $('#wrapper').height($('#myTable').height())
  $('#myTable_info').html('Current Total = '+(count));
}

function toggle(client){
  $("tr").removeClass("hide");
  $(".tablinks").css({ "background-color" : "#f1f1f1"});
  var clicked = $(event.target).attr('id');
  $('#'+clicked).css({ "background-color" : "#989898"});
  var table = document.getElementById("myTable");
  var tr = table.getElementsByTagName("tr");
  for (var i = 0; i < tr.length; i++) {
    var td = tr[i].getElementsByTagName("td")[0];
    if (td) {
      var txtValue = td.textContent || td.innerText;
      if (txtValue != client) {
        $(tr[i]).addClass("hide");
      }
    }
  }
  $('#wrapper').height($('#myTable').height())
  $('#right-button').show();
}

function toggle_all() {
  $("tr").removeClass("hide");
  $(".tablinks").css({ "background-color" : "#f1f1f1"});
  var clicked = $(event.target).attr('id');
  $('#'+clicked).css({ "background-color" : "#989898"});
  $('#wrapper').height($('#myTable').height())
  $('#right-button').hide();
}



function refresh_content(){
  window.location.href = "rerun";
}

function removeFromList(dos, mrn, lname, fname, id) {
  var http = new XMLHttpRequest();
  var url = 'http://smitools.supmed.local/reconcile/remove/'+id
  var record = dos+" "+mrn+" "+lname+", "+fname
  var r = confirm("Are you sure you want to remove: \n"+record)
  if (r == true) {
    var btn = document.createElement("BUTTON");
    var newid = "remove"+id;
    console.log(newid)
    btn.innerHTML = "Undo";
    btn.id = newid;
    btn.addEventListener('click', function() {undo(id, newid)}, false);
    document.getElementById(id).appendChild(btn);
    http.open("GET", url);
    http.send();
  }
}

function undo(id, newid) {
  var http = new XMLHttpRequest();
  var url = 'http://smitools.supmed.local/reconcile/undo/'+id
  http.open("GET", url);
  http.send();
  document.getElementById(newid).remove()
}
