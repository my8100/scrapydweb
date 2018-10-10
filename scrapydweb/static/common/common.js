function my$(selector) {
    if (typeof selector !== 'string' || selector === '') return;
    return document.querySelector(selector)
}


function my$$(selector) {
    if (typeof selector !== 'string' || selector === '') return;
    return document.querySelectorAll(selector)
}


function showLoader() {
    //console.log('showLoader');
    my$('.loader').style = 'display:block';
}


function hideLoader() {
    //console.log('hideLoader');
    my$('.loader').style = 'display:none';
}


function uploadLogfile() {
    //var filename = my$('form')['file'].value;
    var logfile = my$('#file').files[0];
    if(logfile === undefined) {
        alert("Select a log or txt file");
        return;
    }

    var parts = logfile.name.split('.');
    var filetype = parts[parts.length - 1];
    if(['log', 'txt'].indexOf(filetype) == -1) {
        alert("Select a log or txt file");
        return;
    }

    my$('form').submit();
    showLoader();
}


function parseQueryString(url) {
    // history.pushState(null, '', '/scrapyd/');
    var urlParams = {};
    url.replace(
        new RegExp("([^?=&]+)(=([^&]*))?", "g"),
        function($0, $1, $2, $3) {
            urlParams[$1] = $3;
        }
    );
    return urlParams;
}


function setDaemonstatus(node_name, pending, running, finished) {
    if (node_name == '?') {
        my$('#nav_daemonstatus').style.color = 'red';
    } else {
        my$('#nav_daemonstatus').style.color = 'black';
    }
    my$('#nav_node_name').innerText = node_name;
    my$('#nav_pending').innerText = pending;
    my$('#nav_running').innerText = running;
    my$('#nav_finished').innerText = finished;
}


var refresh_daemonstatus_fail_times = 0;
function refreshDaemonstatus(url_daemonstatus) {
    var req = new XMLHttpRequest();
    req.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (this.status == 200) {
                var obj = JSON.parse(this.responseText);
                if(obj.status == 'ok') {
                    refresh_daemonstatus_fail_times = 0;
                    setDaemonstatus(obj.node_name, obj.pending, obj.running, obj.finished)
                } else {
                    refresh_daemonstatus_fail_times += 1;
                    setDaemonstatus('?', '?', '?', '?')
                    if(refresh_daemonstatus_fail_times >= 3 && refresh_daemonstatus_fail_times % 3 == 0){
                        //alert('FAIL to refresh daemonstatus, check '+obj.url);
                        if (window.confirm("FAIL to refresh daemonstatus, open a new tab for details?")) {
                            var win = window.open(obj.url, '_blank');
                            win.focus();
                        }
                    }
                }
            } else {
                refresh_daemonstatus_fail_times += 1;
                setDaemonstatus('?', '?', '?', '?')
                if(refresh_daemonstatus_fail_times >= 3 && refresh_daemonstatus_fail_times % 3 == 0){
                    alert("FAIL to refresh daemonstatus, status code is "+this.status+", check the log of ScrapydWeb");
                }
            }
        }
    };
    req.open("post", url_daemonstatus, Async = true);
    req.send();
}



//https://tuhrig.de/basic-auth-log-out-with-javascript/
//Basic Auth log-out with JavaScript
function logout() {

	// To invalidate a basic auth login:
	//
	// 	1. Call this logout function.
	//	2. It makes a GET request to an URL with false Basic Auth credentials
	//	3. The URL returns a 401 Unauthorized
	// 	4. Forward to some "you-are-logged-out"-page
	// 	5. Done, the Basic Auth header is invalid now

    // Added by llx
    document.querySelector('html').innerHTML = "";

	jQuery.ajax({
            type: "GET",
            url: "/",
            async: false,
            username: "logmeout",
            password: "123456",
            headers: { "Authorization": "Basic xxx" }
	})
	.done(function(){
	    // If we don't get an error, we actually got an error as we expect an 401!
	})
	.fail(function(){
	    // We expect to get an 401 Unauthorized error! In this case we are successfully
            // logged out and we redirect the user.
	    window.location = "/";
    });

    return false;
}
