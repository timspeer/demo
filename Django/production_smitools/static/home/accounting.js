
var fill_cancel = false;
var distribute_cancel = false;

function fill(cancel, url) {
    $.ajax({
        url : url,
        dataType : "text",
        success: function(resp) {
            if (resp == "stop") {
                cancel = true
            };
        }
    });
}

function executeQuery(cancel) {
    $.ajax({
        url : 'ajax',
        dataType : "json",
        success: function(resp) {
            if (cancel) {
                return;
            } else {
                setTimeout(updateTable(resp.providers), 5000);
            };
        }
    });
    setTimeout(executeQuery, 1000);
}

$(document).ready(function () {
    fill(fill_cancel, "fill")
    executeQuery(fill_cancel);
});

function distribute() {
    alert("Files are Being Published")
    fill(distribute_cancel, "distribute")
    executeQuery(distribute_cancel)
}

function updateTable(providers) {
    for (var i=0;i< providers.length;i++) {
        var id = providers[i].id
        var local = providers[i].local_file
        var sharefile = providers[i].sharefile_folder
        var remote = providers[i].published_file
        if (local != null) {
            var ele = document.getElementById(id+"_local");
            ele.innerHTML = local;
        }
        if (sharefile != null) {
            var ele = document.getElementById(id+"_sharefile");
            ele.innerHTML = sharefile;
        }
        if (remote != null) {
            var ele = document.getElementById(id+"_remote_file");
            ele.innerHTML = remote;
        }
    }

}

