# -*- coding: utf-8 -*-
import json
import httplib
import websocket
import ConfigParser
import time
from subprocess import Popen, PIPE
import collections


#chrome_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_path = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
conf_file = "test_url.txt"


def AutoVivification(default_type):
    """
    Implementation of perl's autovivification feature.
    @param default_type:
    @return:
    """
    return collections.defaultdict(lambda: collections.defaultdict(default_type))


def parse_conf_file():
    """
    parse configure file
    @return:
    """
    data = AutoVivification(list)
    config = ConfigParser.RawConfigParser()
    config.read(conf_file)
    for section in config.sections():
        data[section]['http'] = config.get(section, 'http')
        data[section]['spdy'] = config.get(section, 'spdy')
    return data


def pretty_print_json(json_data):
    """
    pretty print json string
    @param json_data:
    """
    print json.dumps(json_data, indent=4, separators=(',', ':'))


def write_json_to_file(json_data, file_name):
    """
    pretty print json string
    @param json_data:
    """
    with open(file_name, 'w+') as output:
        output.write(json.dumps(json_data, indent=4, separators=(',', ':')))


def start_chrome():
    """
    start chrome in debugging mode
    """
    #you can add  "--ignore-certificate-errors" to avoid certificate error
    Popen("%s --ignore-certificate-errors --remote-debugging-port=9222" % chrome_path)
    time.sleep(3)


def stop_chrome():
    """
    kill chrome.exe to free keep-alive connection
    """
    time.sleep(1)
    Popen("taskkill /F /IM chrome.exe")
    time.sleep(2)


def restart_chrome():
    """
    restart chrome
    """
    stop_chrome()
    start_chrome()


def connect_to_chrome():
    """
    connect to chrome
    @return: websockt
    """
    # Chrome runs an HTTP handler listing available tabs
    conn = httplib.HTTPConnection("localhost", 9222)
    conn.request("GET", "/json")
    resp = json.load(conn.getresponse())
    # connect to first tab via the WS debug URL
    return websocket.create_connection(resp[0]['webSocketDebuggerUrl'])


def disconnect_to_chrome(ws):
    """
    disconnect to chrome
    @param ws:
    """
    ws.close()


def calc_page_resources(url):
    """
    calculate page resources
    @param url:
    @return: resources
    """
    ws = connect_to_chrome()
    ws.settimeout(5)
    # Clears browser cache.
    ws.send(json.dumps(dict(
        id=1,
        method='Network.clearBrowserCache'
    )))
    ws.recv()

    # Enables network tracking, network events will now be delivered to the client.
    ws.send(json.dumps(dict(
        id=2,
        method='Network.enable'
    )))
    ws.recv()

    # tell Chrome to navigate to url
    ws.send(json.dumps(dict(
        id=3,
        method='Page.navigate',
        params={'url': url}
    )))
    ws.recv()

    resource = AutoVivification(list)
    result = AutoVivification(int)

    while 1:
        try:
            data = json.loads(ws.recv())
            #pretty_print_json(data)
            req_id = data['params']['requestId']
            if data['method'] == 'Network.requestWillBeSent':
                resource[req_id]['status'] = 0
                resource[req_id]['type'] = '404'

            if data['method'] == 'Network.responseReceived':
                if data['params']['response']['status'] == 200:
                    # load success
                    resource[req_id]['type'] = data['params']['type']
                    resource[req_id]['status'] = 1

            if data['method'] == 'Network.dataReceived':
                resource[req_id]['size'] = data['params']['encodedDataLength']

        except websocket.WebSocketTimeoutException:
            disconnect_to_chrome(ws)
            break
    # reformat resource result
    for req_id in resource:
        res_type = resource[req_id]['type']
        if resource[req_id]['status'] == 1:
            result[res_type]['count'] += 1
            if resource[req_id]['size']:
                result[res_type]['size'] += resource[req_id]['size']
        if resource[req_id]['status'] == 0:
            result[res_type]['count'] += 1
    return result


def calc_page_load_time(url):
    ws = connect_to_chrome()

    # Clears browser cache.
    ws.send(json.dumps(dict(
        id=1,
        method='Network.clearBrowserCache'
    )))
    ws.recv()

    # Enables network tracking, network events will now be delivered to the client.
    ws.send(json.dumps(dict(
        id=2,
        method='Network.enable'
    )))
    ws.recv()

    # enable page domain notice
    ws.send(json.dumps(dict(
        id=3,
        method='Page.enable'
    )))
    ws.recv()

    # tell Chrome to navigate to url
    ws.send(json.dumps(dict(
        id=4,
        method='Page.navigate',
        params={'url': url}
    )))
    ws.recv()

    first_request_time = load_fin_time = dom_time = load_time = 0

    while 1:
        result = json.loads(ws.recv())
        pretty_print_json(result)
        if first_request_time == 0 and "params" in result and "method" in result:
            if result["method"] == "Network.requestWillBeSent":
                first_request_time = result["params"]["timestamp"]
                #print "first_request_time is %f" % first_request_time
        if "method" in result:
            m = result['method']
            if m == "Page.loadEventFired":
                load_fin_time = result["params"]["timestamp"]
                load_time = load_fin_time - first_request_time
                #print "load time is:%f %f" % (load_fin_time, load_time)
            if m == "Page.domContentEventFired":
                dom_content_time = result["params"]["timestamp"]
                dom_time = dom_content_time - first_request_time
                #print "domContentEvent time is:%f %f" % (dom_content_time, dom_time)
            if load_fin_time != 0:
                #print "receive Page.frameStoppedLoading"
                disconnect_to_chrome(ws)
                return {'dom_time': dom_time, 'load_time': load_time}


def main_test():
    """
    main test function
    """
    start_chrome()
    cfg_data = parse_conf_file()
    resource_data = cfg_data
    time_data = AutoVivification(dict)
    repeat_time = 2
    ##step 1: calculate site resources
    #for site in cfg_data:
        #resource_data[site]['resources'] = calc_page_resources(cfg_data[site]['http'])
    #write_json_to_file(resource_data, 'site_resources.txt')
#
    #restart_chrome()
    # step 2: calculate site load_time
    for site in cfg_data:
        all_spdy_dom_time = all_spdy_load_time = all_http_dom_time = all_http_load_time = 0.0
        restart_chrome()
        calc_page_load_time(cfg_data[site]['spdy'])
        print site 
        for i in range(0, repeat_time):
            # test http time
            print "before calc"
            http_time = calc_page_load_time(cfg_data[site]['http'])
            print "after calc"
            if i < repeat_time - 1: 
                all_http_load_time += http_time['load_time']
                all_http_dom_time += http_time['dom_time']
            time.sleep(1)
            print "+++ %s %d times:  http load time: %f, http dom time: %f \n" %(site, i, http_time['load_time'], http_time['dom_time'])
            restart_chrome()
            # test spdy time
            spdy_time = calc_page_load_time(cfg_data[site]['spdy'])
            if i < repeat_time - 1: 
                all_spdy_load_time += spdy_time['load_time']
                all_spdy_dom_time += spdy_time['dom_time']
            time.sleep(1)
            print "+++ %s %d times:  spdy load time: %f, spdy dom time: %f \n" %(site, i, spdy_time['load_time'], spdy_time['dom_time'])

            restart_chrome()

        # calculate time average
        time_data[site]['http']['dom_time'] = all_http_dom_time / (repeat_time-1)
        time_data[site]['http']['load_time'] = all_http_load_time / (repeat_time-1)
        time_data[site]['spdy']['dom_time'] = all_spdy_dom_time / (repeat_time-1)
        time_data[site]['spdy']['load_time'] = all_spdy_load_time / (repeat_time-1)

    write_json_to_file(time_data, 'site_time.txt')
    stop_chrome()

if __name__ == "__main__":
    main_test()
