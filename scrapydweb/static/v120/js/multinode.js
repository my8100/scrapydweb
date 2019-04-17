var checked_amount = 1;


function showCheckboxes(click_outside_close) {
    var checkboxes = my$('#checkboxes');

    if (checkboxes.style.display == 'block') {
        if (!(click_outside_close && checked_amount == 0)) {
            checkboxes.style.display = 'none';
            my$('.multiselect .icon.anchor').style.transform = 'rotate(0deg)';
        }
    } else if (click_outside_close === undefined) {
        checkboxes.style.display = 'block';
        my$('.multiselect .icon.anchor').style.transform = 'rotate(-180deg)';
    }
    if (checked_amount == 0 && checkboxes.style.display == 'none') {
        my$('.selectBox .value').style.border = "1px solid #f56c6c";
    } else if (checkboxes.style.display == 'none') {
        my$('.selectBox .value').style.border = "1px solid #67c23a";
    } else {
        my$('.selectBox .value').style.border = "1px solid #409EFF";  // blue
    }

    // If click_outside_close and execute animate(), click the HELP section would trigger scrolling to bottom
    if (click_outside_close === undefined) {
        goContentBottom();
    }
}


function checkCheckboxes(SCRAPYD_SERVERS_AMOUNT) {
    checked_amount = my$$('#nodes_checkboxes input[type="checkbox"]:checked').length;
    my$('input[name="checked_amount"]').value = checked_amount;
    //console.log('length: ' + my$$('#nodes_checkboxes input[type="checkbox"]:checked').length);
    //console.log('checked_amount for check: ' + checked_amount);
    console.log('input checked_amount: ' + my$('input[name="checked_amount"]').value);

    //my$('.selectBox .value').style.border = "1px solid #dcdfe6"; // gray
    if (checked_amount == 0) {
        my$('#selected_nodes_statement').innerText = "Select at least one node";
        my$('.multiselect .form-item-error').style.display = 'block';
        my$('#checkboxes').style.display = 'block';
        my$('#checkboxes').style.border = "1px solid #f56c6c";  // red
        my$('#checkboxes').style.borderTopWidth = '0';
        goContentBottom();
    } else {
        my$('.multiselect .form-item-error').style.display = 'none';
        my$('#checkboxes').style.border = "1px solid #67c23a";  // green
        my$('#checkboxes').style.borderTopWidth = '0';

        if (checked_amount == 1) {
            var input_id = my$('#nodes_checkboxes input[type="checkbox"]:checked').id.slice(9);
            // my$('#selected_nodes_statement').innerText = my$('#label_'+input_id).textContent.replace(/^\s+|\s+$/g, '');
            var statement = my$('#label_'+input_id).textContent.replace(/^\s+|\s+$/g, '');
            if (statement.length > 35) {
                my$('#selected_nodes_statement').innerText = statement.slice(0, 16) + '...' + statement.slice(-16, );
            } else {
                my$('#selected_nodes_statement').innerText = statement;
            }
        } else if (checked_amount == SCRAPYD_SERVERS_AMOUNT) {
            my$('#selected_nodes_statement').innerText = "All "+SCRAPYD_SERVERS_AMOUNT+" nodes selected";
        } else {
            my$('#selected_nodes_statement').innerText = checked_amount+"/"+SCRAPYD_SERVERS_AMOUNT+" nodes selected";
        }
    }
    my$('#selected_nodes_statement').selected = "selected"; //For navigate back
    //console.log(my$('#selected_nodes_statement').innerText);
}


function invertSelection() {
    var boxes = my$$('tbody input[type="checkbox"]');
    for (var idx in boxes) {
        boxes[idx].checked = !boxes[idx].checked;
    }
}


function passToServers() {
    var checked_amount = my$$('tbody input[type="checkbox"]:checked').length;
    if (checked_amount == 0) {
        var r = confirm("None of the nodes are selected, continue?");
        if (r == false) {
            return;
        }
    }

    my$('form').action = url_servers;
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