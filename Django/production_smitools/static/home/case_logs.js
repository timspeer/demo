$(document).ready( function () {
    var days = new Array();
    var date = new Date();
    var dates = new Array();
    date.setDate(date.getDate() - 46);
    weekday = date.getDay();
    var month = date.toLocaleString('default', { month : 'long'});
    $('#month-name').text(month)
    for (var i = 0; i < 46; i++) {
    date.setDate(date.getDate() + 1);
    var format_date = date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year : 'numeric' })
    dates.push(format_date)
    day = date.getDate()
    days.push(day)
    }
    var cal_days = document.getElementsByClassName("calendar__day day")
    for (i=0; i < days.length; i++) {
    cal_days[weekday].getElementsByClassName("day")[0].textContent = days[i]
    cal_days[weekday].id = dates[i]
    weekday = weekday + 1;
    };
  });

  $(document).ready( function () {
    var data = DATA.split("^")
    for (var i=0; i<data.length; i++) {
    data[i] = data[i].split("|")
    }
    for (i=0; i < data.length; i++) {
    var set = data[i]
    var ele = document.getElementById(set[1])
    if (ele != null) {
        var txt = "Keyed In PHI: " + set[3] + "\r\nCases Entered: " + set[4] + "\r\n"
        var div = document.createElement('div');
        var fac = document.createElement('p');
        var par = document.createElement('p');
        fac.textContent = set[2]
        fac.style.fontWeight = 'bold'
        par.textContent = txt
        div.className = set[0]+" "+set[2]
        ele.appendChild(div)
        div.appendChild(fac)
        div.appendChild(par)
    }
    };
  });
  
  $(document).ready( function () {
    $(".tablinks.facilities").css({ display: 'none' });
    $("p").css({ display: 'none' })
    var cell_data = document.getElementsByClassName("calendar__day day")
    for (i=0;i<cell_data.length;i++) {
    var phi_num = 0
    var batch_num = 0
    var para = cell_data[i].getElementsByTagName('p')
    for (j=0;j<para.length;j++) {
        var cell_array = para[j].textContent.split('\r\n')
        if (cell_array.length > 1) { 
            phi_num = phi_num + parseInt(cell_array[0].split(":")[1])
            batch_num = batch_num + parseInt(cell_array[1].split(":")[1])
        }
    }
    var par = document.createElement('p')
    var par2 = document.createElement('p')
    par.textContent = "Total Cases in PHI\r\n" + phi_num
    par2.textContent = "Total Batches\r\n" + batch_num
    par.className = 'total'
    par2.className = 'total'
    if (phi_num != 0) {
    cell_data[i].appendChild(par)
    }
    if (batch_num != 0) {
    cell_data[i].appendChild(par2)
    }
    };
  });

  function case_log_toggle(client) {
    $(".tablinks.facilities").css({ display: 'none' });
    $(".calendar").css({ "margin-top" : "300px" })
    $(".tablinks").css({ "background-color" : "#f1f1f1"});
    $(".tablinks.facilities."+client).css({ display: '' });
    $("p").css({ display : 'none' })
    $("."+client+" > p").css({ display : '' })
    var clicked = $(event.target).attr("id")
    var id = document.getElementById(clicked)
    if (id.style.backgroundColor === "rgb(152, 152, 152)") {
    id.style.backgroundColor = null;
    } else {
    id.style.backgroundColor = "rgb(152, 152, 152)";
    };
  };
  
  function case_log_toggle_facilities(fac) {
    $("p").css({ display : 'none' })
    $(".tablinks.facilities").css({ "background-color" : "#f1f1f1"});
    var fac_list = document.getElementsByClassName(fac)
    for (i=0;i<fac_list.length;i++) {
    par = fac_list[i].getElementsByTagName('p')
    for (j=0;j<fac_list.length;j++) {
        if (par[j]) {
        par[j].style.display = ''
        }
    }
    }
    var clicked = $(event.target).attr('class')
    document.getElementsByClassName(clicked)[0].style.backgroundColor = "rgb(152, 152, 152)";
  };

  function case_toggle_all () {
    $(".tablinks").css({ "background-color" : "#f1f1f1"});
    $(".calendar").css({ "margin-top" : "100px" })
    $("p").css({ display: 'none' })
    $(".tablinks.facilities").css({ display: 'none' });
    $(".total").css({ display: '' })
    var clicked = $(event.target).attr("id")
      var id = document.getElementById(clicked)
      if (id.style.backgroundColor === "rgb(152, 152, 152)") {
        id.style.backgroundColor = null;
      } else {
        id.style.backgroundColor = "rgb(152, 152, 152)";
      }
  }