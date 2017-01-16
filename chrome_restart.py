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
    Popen("%s --remote-debugging-port=9222 %s" % (chrome_path, "https://www.helloworlds.cc"))
    time.sleep(1)


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




def main_test():
    """
    main test function
    """
 
    cfg_data = parse_conf_file()
    resource_data = cfg_data
    time_data = AutoVivification(dict)
    repeat_time = 10
    ##step 1: calculate site resources
    #for site in cfg_data:
        #resource_data[site]['resources'] = calc_page_resources(cfg_data[site]['http'])
    #write_json_to_file(resource_data, 'site_resources.txt')
#
    #restart_chrome()

    for i in range(0, repeat_time):
        restart_chrome()



if __name__ == "__main__":
    main_test()
