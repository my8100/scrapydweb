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



function setColor(LAST_LOG_ALERT_SECONDS, font_or_bg) {
    var cew_count_arr = new Array('log_critical_count', 'log_error_count', 'log_warning_count');
    var log_count_arr = new Array('retry_count', 'redirect_count', 'ignore_count');
    var last_time_arr = new Array('last_crawl', 'last_scrape', 'last_log');

    for (idx in cew_count_arr) {
        item = cew_count_arr[idx];
        if (my$('#' + item).innerHTML != '0') {
            if (font_or_bg == 'font') {
                my$('#' + item).style.color = 'red';
                my$('#' + item).innerHTML = '<strong style="font-size: 30px; color: red;">' + my$('#' + item).innerHTML + '</strong>';
            } else {
                my$('#' + item).style.backgroundColor = 'red';
            }
        }
    }

    for (idx in log_count_arr) {
        item = log_count_arr[idx];
        if (my$('#' + item).innerHTML != '0') {
            if (font_or_bg == 'font') {
                my$('#' + item).innerHTML = '<strong style="font-size: 30px; color: orange;">' + my$('#' + item).innerHTML + '</strong>';
            } else {
                my$('#' + item).style.backgroundColor = 'orange';
            }
        }
    }

    for (idx in last_time_arr) {
        item = last_time_arr[idx];
        x_secs_ago = my$('#' + item).innerHTML.match(/\d+/g)[0];
        if (parseInt(x_secs_ago) > LAST_LOG_ALERT_SECONDS) {
            if (font_or_bg == 'font') {
                my$('#' + item).innerHTML = '<strong style="font-size: 30px; color: #409EFF;">' + my$('#' + item).innerHTML + '</strong>';
            } else {
                my$('#' + item).style.backgroundColor = 'yellow';
            }
        }
    }
}


function setTime() {
    var now_timestamp = Date.now() / 1000;
    my$('#last_crawl').innerHTML = Math.ceil((now_timestamp - last_crawl_timestamp)) + ' seconds ago';
    my$('#last_scrape').innerHTML = Math.ceil((now_timestamp - last_scrape_timestamp)) + ' seconds ago';
    my$('#last_log').innerHTML = Math.ceil((now_timestamp - last_log_timestamp)) + ' seconds ago';
    my$('#current_time').innerHTML = Date();
}


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
    for (idx in id_of_tabs) {
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
