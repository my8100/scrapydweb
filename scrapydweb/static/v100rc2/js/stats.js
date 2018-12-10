(function() {
    var throttle = function(type, name, obj) {
        obj = obj || window;
        var running = false;
        var func = function() {
            if (running) { return; }
            running = true;
             requestAnimationFrame(function() {
                obj.dispatchEvent(new CustomEvent(name));
                running = false;
            });
        };
        obj.addEventListener(type, func);
    };

    /* init - you can init any event */
    throttle("resize", "optimizedResize");
})();



function setColor(size) {

    var cew_count_arr = new Array('log_critical_count', 'log_error_count', 'log_warning_count');
    for (var idx in cew_count_arr) {
        var ele = my$('#' + cew_count_arr[idx]);
        if (ele.innerText != '0') {
            ele.innerHTML = '<strong style="font-size: ' + size + 'px; color: red;">' + ele.innerText + '</strong>';
        }
    }

    var log_count_arr = new Array('log_retry_count', 'log_redirect_count', 'log_ignore_count');
    for (var idx in log_count_arr) {
        var ele = my$('#' + log_count_arr[idx]);
        if (ele.innerText != '0') {
            ele.innerHTML = '<strong style="font-size: ' + size + 'px; color: orange;">' + ele.innerText + '</strong>';
        }
    }

    var latest_time_arr = new Array('latest_crawl', 'latest_scrape', 'latest_log');
    var latest_timestamp_arr = new Array(latest_crawl_timestamp, latest_scrape_timestamp, latest_log_timestamp);
    var now_timestamp = Date.now() / 1000;
    for (var idx in latest_time_arr) {
        var ele = my$('#' + latest_time_arr[idx]);
        var seconds = Math.ceil(now_timestamp - latest_timestamp_arr[idx]);
        var result = timeAgo(seconds);
        // console.log(seconds, result);

        if (result.indexOf('second') == -1 ) {
            ele.innerHTML = '<strong style="font-size: ' + size + 'px; color: #409EFF;">' + result + '</strong>';
        } else {
            ele.innerText = result;
        }
    }
}


// https://stackoverflow.com/a/23259289/10517783
var timeAgo = function(seconds) {
    var intervalType;

    var interval = Math.floor(seconds / 31536000);
    if (interval >= 1) {
        intervalType = 'year';
    } else {
        interval = Math.floor(seconds / 2592000);
        if (interval >= 1) {
            intervalType = 'month';
        } else {
            interval = Math.floor(seconds / 86400);
            if (interval >= 1) {
                intervalType = 'day';
            } else {
                interval = Math.floor(seconds / 3600);
                if (interval >= 1) {
                    intervalType = "hour";
                } else {
                    interval = Math.floor(seconds / 60);
                    if (interval >= 1) {
                        intervalType = "minute";
                    } else {
                        interval = seconds;
                        intervalType = "second";
                    }
                }
            }
        }
    }

    if (interval < -1 || interval === 0 || interval > 1) {
        intervalType += 's ago';
    } else {
        intervalType += ' ago';
    }

    return interval + ' ' + intervalType;
};


function displaySwitcher(id1, id2) {
    ele1 = my$('#' + id1);
    // ele2 = my$('#' + id2);
    if (ele1.style.display == 'none') {
        // ele1.style.display = 'block';
        ele1.style.display = '';
        if(typeof id2 !== 'undefined') {
            my$('#' + id2).style.display = 'none';
        }
    } else {
        ele1.style.display = 'none';
        if(typeof id2 !== 'undefined') {
            my$('#' + id2).style.display = '';
        }
    }
}


function draw(chart, datas, title, label_1, index_1, label_2, index_2) {
    // data = [["2000-06-05 01-01-01",116, 216],["2000-06-06 02-02-02",129, 229]];
    chart.setOption(option = {
        title: {
            text: title
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            data: datas.map(function (item) {
                return item[0];
            }),
        },
        yAxis: {
            splitLine: {
                show: true
            }
        },
        toolbox: {
            left: 'center',
            feature: {
                // dataZoom: {
                    // yAxisIndex: 'none'
                // },
                restore: {},
                saveAsImage: {}
            }
        },
        dataZoom: [{
            startValue: '2018-01-01 00-00-01'
        }, {
            type: 'inside'
        }],

        series: [{
            name: label_1,
            type: 'line',
            data: datas.map(function (item) {
                return item[index_1];
            }),
        },
        {
            name: label_2,
            type: 'line',
            data: datas.map(function (item) {
                return item[index_2];
            }),
        }
        ]
    });
}


function switchTab(id) {
    for (var idx in id_of_tabs) {
        i = id_of_tabs[idx];
        var btn = my$('#btn_' + i);
        var tab = my$('#tab_' + i);
        if (i == id) {
            btn.className = 'submenu submenu-pressed';
            if (i == 'chart') {
                tab.style.visibility = 'visible';
            } else {
                tab.style.display = '';
            }
        } else {
            btn.className = 'submenu';
            if (i == 'chart') {
                tab.style.visibility = 'hidden';
            } else {
                tab.style.display = 'none';
            }
        }
    }
}
