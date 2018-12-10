# coding: utf8
import time
import datetime
import re


pattern_datetime = r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}'
# 2018-06-25 18:12:49 [scrapy.extensions.logstats] INFO:
# Crawled 2318 pages (at 2 pages/min), scraped 68438 items (at 60 items/min)
pattern_datas = re.compile(r"""\n(?P<time_>%s).*?
                            Crawled\s(?P<pages>\d+)\s+pages\s
                            \(at\s(?P<pages_min>\d+)\spages/min\),\s
                            scraped\s(?P<items>\d+)\sitems\s
                            \(at\s(?P<items_min>\d+)\sitems/min\)
                            """ % pattern_datetime, re.X)

patterns = [
    r'\]\sCRITICAL:',
    r'\]\sERROR:',
    r'\]\sWARNING:',
    r':\sRedirecting\s\(',
    r':\sRetrying\s<',
    r':\sIgnoring\sresponse\s<',
]
pattern_logs_count_list = []
for p in patterns:
    pattern = re.compile(r"""\n
                            (\d{4}[^\n]*?%s.*?)
                            (?=\n\d{4}[^\n]*?(?:DEBUG|INFO|WARNING|ERROR|CRITICAL))
                        """ % p, re.S | re.X)
    pattern_logs_count_list.append(pattern)


def parse_log(text, kwargs):
    # fake_time = '2018-01-01 00:00:01'
    fake_time = time.strftime('%Y-%m-%d %H:%M:%S')
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
    # For compatibility with Python 2, str(time_) to avoid [u'2018-08-22 18:43:05', 0, 0, 0, 0] in JavaScript
    kwargs['datas'] = [[str(time_), int(pages), int(pages_min), int(items), int(items_min)]
                       for (time_, pages, pages_min, items, items_min) in datas]
    kwargs['crawled_pages'] = int(datas[-1][1]) if datas else 0
    kwargs['scraped_items'] = int(datas[-1][3]) if datas else 0

    # Extract only last log
    latest_tuples = [
        # ('resuming_crawl', 'Resuming\scrawl'),
        ('latest_offsite', r'Filtered\soffsite'),
        ('latest_duplicate', r'Filtered\sduplicate'),
        ('latest_crawl', r'Crawled\s\(\d+'),
        ('latest_scrape', r'Scraped\sfrom\s'),
        ('latest_item', r'^\{.*\}'),
        ('latest_stat', r'Crawled\s\d+\spages'),
    ]
    latest_matches = [('resuming_crawl', re_search_final_match(r'Resuming\scrawl', step=1))]
    for k, v in latest_tuples:
        ret = re_search_final_match(v)
        latest_matches.append((k, ret))
        if k == 'latest_crawl':
            latest_crawl_datetime = datetime.datetime.strptime(ret[:19] or fake_time, '%Y-%m-%d %H:%M:%S')
        elif k == 'latest_scrape':
            latest_scrape_datetime = datetime.datetime.strptime(ret[:19] or fake_time, '%Y-%m-%d %H:%M:%S')

    kwargs['latest_crawl_timestamp'] = time.mktime(latest_crawl_datetime.timetuple())
    kwargs['latest_scrape_timestamp'] = time.mktime(latest_scrape_datetime.timetuple())
    kwargs['latest_matches'] = latest_matches

    # Extract log count and details
    logs_count_tuples = [
        ('critical_logs', 'log_critical_logs_details', 'log_critical_count'),
        ('error_logs', 'log_error_logs_details', 'log_error_count'),
        ('warning_logs', 'log_warning_logs_details', 'log_warning_count'),
        ('redirect_logs', 'redirect_logs_details', 'log_redirect_count'),
        ('retry_logs', 'retry_logs_details', 'log_retry_count'),
        ('ignore_logs', 'ignore_logs_details', 'log_ignore_count'),
    ]
    text += '2018 DEBUG'
    re_matches = []
    for idx, (pattern, (log_title, log_details, log_count)) in enumerate(
            zip(pattern_logs_count_list, logs_count_tuples)):
        matches = pattern.findall(text)
        count = len(matches)
        kwargs[log_count] = count

        re_matches.append({
            'log_title': log_title,
            'log_details': log_details,
            'count': count,
            'line': matches[-1] if matches else '',
            # 'lines': '\n'.join(matches) #if idx < 3 else '',
            'lines': matches
        })
    kwargs['re_matches'] = re_matches

    # 'finish_reason': 'closespider_timeout',
    m = re.search(r":\s'(.*?)'", re_search_final_match(r"'finish_reason'"))
    kwargs['finish_reason'] = m.group(1) if m else ''

    if kwargs['finish_reason']:
        m = re.search(r":\s(\d+)", re_search_final_match(r"'downloader/response_status_count/200'"))
        kwargs['crawled_pages'] = max(kwargs['crawled_pages'], int(m.group(1)) if m else 0)
        m = re.search(r":\s(\d+)", re_search_final_match(r"'item_scraped_count'"))
        kwargs['scraped_items'] = (int(m.group(1)) if m else 0) or kwargs['scraped_items']

        m = re.search(r":\s(\d+)", re_search_final_match(r"'log_count/CRITICAL'"))
        kwargs['log_critical_count'] = int(m.group(1)) if m else kwargs['log_critical_count']
        m = re.search(r":\s(\d+)", re_search_final_match(r"'log_count/ERROR'"))
        kwargs['log_error_count'] = int(m.group(1)) if m else kwargs['log_error_count']
        m = re.search(r":\s(\d+)", re_search_final_match(r"'log_count/WARNING'"))
        kwargs['log_warning_count'] = int(m.group(1)) if m else kwargs['log_warning_count']

        m_301 = re.search(r":\s(\d+)", re_search_final_match(r"'downloader/response_status_count/301'"))
        count_301 = int(m_301.group(1)) if m_301 else 0
        m_302 = re.search(r":\s(\d+)", re_search_final_match(r"'downloader/response_status_count/302'"))
        count_302 = int(m_302.group(1)) if m_302 else 0
        kwargs['log_redirect_count'] = (count_301 + count_302) or kwargs['log_redirect_count']

        m = re.search(r":\s(\d+)", re_search_final_match(r"'retry/count'"))
        kwargs['log_retry_count'] = int(m.group(1)) if m else kwargs['log_retry_count']
        m = re.search(r":\s(\d+)", re_search_final_match(r"'httperror/response_ignored_count'"))
        kwargs['log_ignore_count'] = int(m.group(1)) if m else kwargs['log_ignore_count']
