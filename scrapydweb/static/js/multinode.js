var expanded = true;

function showCheckboxes() {
    var checkboxes = my$('#checkboxes');
    if (!expanded) {
        checkboxes.style.display = 'block';
        expanded = true;

    } else {
        checkboxes.style.display = 'none';
        expanded = false;

    }
}


var checked_amount = 1;
// var SCRAPYD_SERVERS_AMOUNT = {{ SCRAPYD_SERVERS|length }};

function checkCheckboxes(SCRAPYD_SERVERS_AMOUNT) {
    checked_amount = my$$('#nodes_checkboxes input[type="checkbox"]:checked').length;
    my$('input[name="checked_amount"]').value = checked_amount;
    console.log(my$('input[name="checked_amount"]').value);

    if (checked_amount == 0) {
        my$('#selected_nodes_statement').innerText = "Select at least one node";
    } else if (checked_amount == 1) {
        var input_id = my$('#nodes_checkboxes input[type="checkbox"]:checked').id.slice(9, );
        my$('#selected_nodes_statement').innerText = my$('#label_'+input_id).textContent.replace(/^\s+|\s+$/g, '');
    } else if (checked_amount == SCRAPYD_SERVERS_AMOUNT) {
        my$('#selected_nodes_statement').innerText = "All "+SCRAPYD_SERVERS_AMOUNT+" nodes selected";
    } else {
        my$('#selected_nodes_statement').innerText = checked_amount+"/"+SCRAPYD_SERVERS_AMOUNT+" nodes selected";
    }
    my$('#selected_nodes_statement').selected = "selected"; //For navigate back
    console.log(my$('#selected_nodes_statement').innerText);
}


function invertSelection() {
    var boxes = my$$('tbody input[type="checkbox"]');
    for (idx in boxes) {
        boxes[idx].checked = !boxes[idx].checked;
    }
}


function passToOverview() {
    var checked_amount = my$$('tbody input[type="checkbox"]:checked').length;
    if (checked_amount == 0) {
        var r = confirm("NO nodes selected, continue?");
        if(r == false) {
            return;
        }
    }

    my$('form').action = url_overview;
    my$('form').submit();
}


function multinodeRunSpider() {
    var checked_amount = my$$('tbody input[type="checkbox"]:checked').length;
    if (checked_amount == 0) {
        alert("Select at least one node");
        return;
    }
    my$('form').action = url_schedule;
    my$('form').submit();
}