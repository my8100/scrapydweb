# coding: utf8
import time
import datetime
import re


pattern_datetime = '\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}'
# 2018-06-25 18:12:49 [scrapy.extensions.logstats] INFO: Crawled 2318 pages (at 2 pages/min), scraped 68438 items (at 60 items/min)
pattern_datas = re.compile(r"""\n(?P<time_>%s).*?
                            Crawled\s(?P<pages>\d+)\s+pages\s
                            \(at\s(?P<pages_min>\d+)\spages/min\),\s
                            scraped\s(?P<items>\d+)\sitems\s
                            \(at\s(?P<items_min>\d+)\sitems/min\)
                            """ % pattern_datetime, re.X)

patterns = [
    '\]\sCRITICAL:',
    '\]\sERROR:',
    '\]\sWARNING:',
    'Retrying\s<',
    'Redirecting\s\(',
    'Ignoring\sresponse\s<',
]
pattern_logs_count_list = []
for p in patterns:
    pattern = re.compile(r"""\n
                            (\d{4}[^\n]*?%s.*?)
                            (?=\n\d{4}[^\n]*?(?:DEBUG|INFO|WARNING|ERROR|CRITICAL))
                        """ % p, re.S | re.X)
    pattern_logs_count_list.append(pattern)


def parse_log(text, kwargs):
    fake_time = '2018-01-01 00:00:01'
    lines = re.split('\r*\n', text)

    def re_search_final_match(pattern, default='', step=-1):
        for line in lines[::step]:
            m = re.search(pattern, line)
            if m:
                return line
        else:
            return default

    kwargs['first_log_time'] = re_search_final_match(r'^%s' % pattern_datetime, step=1)[:19] or fake_time
    kwargs['latest_log_time'] = re_search_final_match(r'^%s' % pattern_datetime)[:19] or fake_time
    first_log_datetime = datetime.datetime.strptime(kwargs['first_log_time'], '%Y-%m-%d %H:%M:%S')
    latest_log_datetime = datetime.datetime.strptime(kwargs['latest_log_time'], '%Y-%m-%d %H:%M:%S')
    kwargs['latest_log_timestamp'] = time.mktime(latest_log_datetime.timetuple())
    kwargs['elasped'] = str(latest_log_datetime - first_log_datetime)

    kwargs['head_lines'] = '\n'.join(lines[:50])
    kwargs['tail_lines'] = '\n'.join(lines[-50:])

    # Extract datas for chart
    datas = pattern_datas.findall(text)
    # str(time_) to avoid [u'2018-08-22 18:43:05', 0, 0, 0, 0] in js using python2
    kwargs['datas'] = [[str(time_), int(pages), int(pages_min), int(items), int(items_min)]
                       for (time_, pages, pages_min, items, items_min) in datas]
    kwargs['crawled_pages'] = datas[-1][1] if datas else 0
    kwargs['scraped_items'] = datas[-1][3] if datas else 0

    # Extract only last log
    latest_tuples = [
        # ('resuming_crawl', 'Resuming\scrawl'),
        ('latest_offsite', 'Filtered\soffsite'),
        ('latest_duplicate', 'Filtered\sduplicate'),
        ('latest_crawl', 'Crawled\s\(\d+'),
        ('latest_scrape', 'Scraped\sfrom\s'),
        ('latest_item', '^\{.*\}'),
        ('latest_stat', 'Crawled\s\d+\spages'),
    ]
    latest_matchs = [('resuming_crawl', re_search_final_match('Resuming\scrawl', step=1))]
    for k, v in latest_tuples:
        ret = re_search_final_match(v)
        latest_matchs.append((k, ret))
        if k == 'latest_crawl':
            latest_crawl_datetime = datetime.datetime.strptime(ret[:19] or fake_time, '%Y-%m-%d %H:%M:%S')
        elif k == 'latest_scrape':
            latest_scrape_datetime = datetime.datetime.strptime(ret[:19] or fake_time, '%Y-%m-%d %H:%M:%S')

    kwargs['latest_crawl_timestamp'] = time.mktime(latest_crawl_datetime.timetuple())
    kwargs['latest_scrape_timestamp'] = time.mktime(latest_scrape_datetime.timetuple())
    kwargs['latest_matchs'] = latest_matchs

    # Extract log count and details
    logs_count_tuples = [
        ('log_critical_logs', 'log_critical_logs_details', 'log_critical_count'),
        ('log_error_logs', 'log_error_logs_details', 'log_error_count'),
        ('log_warning_logs', 'log_warning_logs_details', 'log_warning_count'),
        ('retry_logs', 'retry_logs_details', 'retry_count'),
        ('redirect_logs', 'redirect_logs_details', 'redirect_count'),
        ('ignore_logs', 'ignore_logs_details', 'ignore_count'),
    ]
    text += '2018 DEBUG'
    re_matchs = []
    for idx, (pattern, (log_title, log_details, log_count)) in enumerate(
            zip(pattern_logs_count_list, logs_count_tuples)):
        matchs = pattern.findall(text)
        count = len(matchs)
        kwargs[log_count] = count

        re_matchs.append({
            'log_title': log_title,
            'log_details': log_details,
            'count': count,
            'line': matchs[-1] if matchs else '',
            # 'lines': '\n'.join(matchs) #if idx < 3 else '',
            'lines': matchs
        })
    kwargs['re_matchs'] = re_matchs

    # 'finish_reason': 'closespider_timeout',
    m = re.search(r":\s'(.*?)'", re_search_final_match(r"'finish_reason'"))
    kwargs['finish_reason'] = m.group(1) if m else ''
