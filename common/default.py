import sys
from datetime import datetime
import time
import json
import socket
import os
import yaml
from time import sleep
import re


def get_hostname():
    return socket.gethostname()


def get_date():
    """
    Obtains current date in "%Y-%m-%d" format

    Examples:
        #>>> get_date()

        '2017-08-22 20:34:54,584'

    @retval string A consistent-length date date string
    """
    date_format = datetime.strftime(datetime.now(), "%Y-%m-%d")
    return date_format


def get_timestamp():
    """
    Obtains current timestamp in standard format with milliseconds

    Examples:
        >>> get_timestamp()

        '2017-08-22 20:34:54,584'

    @retval string A consistent-length date and time string
    """
    date_format = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S,%f").__str__()[:-3]
    return date_format


def log_to_disk(method, msg="", file=None, lvl="INFO", kv="", debug=False):
    """
    Logs to disk
    Outputs to console
    """

    continue_logging = True

    # Check if we should log debug lines
    # app_debug is defined within the calling application
    # and is defined in the app yaml file as app_conf['debug']
    if debug is True and app_debug is False:
        continue_logging = False

    if continue_logging is True:

        # Initialize variables
        successful_write = False
        opened_file = False

        # Change default logfile value
        if file is None:
             file = app_logfile

        # convert lvl to upper and autospace for INFO vs ERROR
        lvl = lvl.upper()
        if len(lvl) == 4:
            if debug is True:
                lvl = " [" + lvl + "]:[DEBUG]  "
            else:
                lvl = " [" + lvl + "]  "
        else:
            if debug is True:
                lvl = " [" + lvl + "]:[DEBUG] "
            else:
                lvl = " [" + lvl + "] "

        # modify spacer
        if msg == "" and kv != "":
            spacer = " -"
        else:
            spacer = " - "

        # write to file
        open_attempt = 0
        write_attempt = 0
        max_attempts = 3

        # Define and print(output)
        output = get_timestamp() + lvl + app_name + "::" \
                 + method + spacer + msg + kv
        print(output)

        # Define logging output with \n
        output = output + "\n"

        # Keep trying to open and write for max_attempts
        while open_attempt != max_attempts and write_attempt != max_attempts:

            # attempt to open file
            try:
                opened_file = open(file, "a")
            except Exception as e:
                print('Unable to open file at the moment:' + e.__str__())
                open_attempt += 1
                sleep(0.1)

            # attempt to write to file
            if opened_file:
                try:
                    successful_write = opened_file.write(output)
                except Exception as e:
                    print('Unable to write to file at the moment:'
                          + e.__str__())
                    write_attempt += 1
                    sleep(0.1)

            if opened_file:
                opened_file.close()

            if successful_write:
                write_attempt = max_attempts


def kvalue(**kwargs):
    """
    Converts kwargs to key=value space delimited string
    """
    text = ""
    for key in kwargs:
        value = kwargs[key]
        value = value.__str__()
        value = value.replace('"', "'")
        text += ' %s="%s"' % (key, value)

    return text


def append_json_dict(dict1, prepend_string, dict2, append_string):

    # add prepend_string and append_string to dict2, make dict1 a str
    dict1_str = dict1.__str__()
    #print(dict1_str)
    dict2_str = prepend_string + dict2.__str__() + append_string
    #print(dict2_str)

    # account for JSON output which doesn't quote True, None, False
    re_parse_1 = re.compile(r"': (?P<unquoted>[A-Za-z]+)")
    re_parse_2 = re.compile(r"': (?P<unquoted>[A-Za-z]+)")
    dict1_parsed_str = re_parse_1.sub(r"': '\g<unquoted>'", dict1_str)
    dict2_parsed_str = re_parse_2.sub(r"': '\g<unquoted>'", dict2_str)

    # replace single with double quotes so that json.loads will parse correctly
    dict1_escapedquote_str = dict1_parsed_str.replace('"', '\\"')
    dict1_doublequote_str = dict1_escapedquote_str.replace("'", '"')
    #print(dict1_doublequote_str)
    dict2_escapedquote_str = dict2_parsed_str.replace('"', '\\"')
    dict2_doublequote_str = dict2_escapedquote_str.replace("'", '"')
    #print(dict2_doublequote_str)

    dict1_final = None
    # error handling for parsing json from (prepend_string,dict1,append_string)
    try:
        dict1_final = json.loads(dict1_doublequote_str)
    except ValueError as e:
        print('Unable to parse(prepend_string,dict1,append_string) into JSON: ' + e.__str__())

    dict2_final = None
    # error handling for parsing json from (prepend_string,dict2,append_string)
    try:
        dict2_final = json.loads(dict2_doublequote_str)
    except ValueError as e:
        print('Unable to parse(prepend_string,dict2,append_string) into JSON: ' + e.__str__())

    if dict1_final is not None and dict1_final is not None:
        merged_dict = None
        # error handling for joining dictionaries
        try:
            merged_dict = dict(dict1_final, **dict2_final)
        except ValueError as e:
            print('Unable to merge dictionaries (dict1, dict2) into JSON: ' + e.__str__())

    # Return merged dictionary
    if 'merged_dict' is not None:
        return merged_dict
    else:
        return "Error: append_json_dict"


def grab_json_from_disk(file):
    """
    Grabs rule from disk and error handles improper JSON syntax
    """
    disk_json = None
    with open(file) as disk_text:
        try:
            disk_json = json.load(disk_text)
        except ValueError as e:
            log_to_disk('JSONParsing',
                        lvl='ERROR',
                        msg='Unable to parse JSON: '+e.__str__())
        if 'disk_json' in locals():
            return disk_json


def grab_yaml_from_disk(file):
    """
    Grabs rule from disk and error handles improper YAML syntax
    """
    disk_yaml = None
    with open(file) as disk_text:
        try:
            disk_yaml = yaml.load(disk_text)
        except Exception as e:
            print('Unable to parse YAML: '+e.__str__())
        if disk_yaml:
            return disk_yaml


def grab_runtime_from_disk(file):

    token = None

    # Attempt to grab from disk
    try:
        token = grab_json_from_disk(file)
    except ValueError as e:
        log_to_disk('Token',
                    lvl='ERROR',
                    msg='TokenError',
                    kv=kvalue(exception=e))
        log_to_disk('Token',
                    lvl="ERROR",
                    msg="NoToken - Unable to obtain token",
                    kv=kvalue(token_runtime_file=file))

    # Proceed if we could obtain token
    if token is not None:
        token = token['token']
        if token['type'] == 'personal':
                return token
        if token['type'] == 'host':
            if token['host'] == get_hostname():
                return token
            else:
                raise NameError("This machine's hostname does "
                                "not match token hostname")


def try_request(f_url, f_headers, log_category, error_msg,
                log_key, log_value, f_dict, json_data="", m="get"):
    """
    Custom function to error handle Requests and output logging
    in a standardized format for Alexis

    Attributes:
        f_url (str): url for requests.get
        f_headers (dict): auth header in json format
        log_category (str): for logging, e.g. 'Poll' in "Poller::Poll"
        error_msg (str): descriptive error message if request fails
        log_key (str): key which ties all the log events together for reporting
                    e.g. feed_name, problem_id in Poller
        log_value (str): unique value for the log_key
                    e.g. "Test_AllOpenProblems_Syn.Day" -> feed_name value
                    e.g. "6685385694655871934"          -> problem_id value
        f_dict (dict): dictionary to store results
               note: must be defined before this function is called
        m (str): get, post, put, delete
    """

    # Attempt requests
    response = None

    # Determine method type
    if m == "get":
        requests_type = requests.get
    if m == "post":
        requests_type = requests.post
    if m == "put":
        requests_type = requests.put
    if m == "delete":
        requests_type = requests.delete

    try:
        if json_data == "":
            response = requests_type(f_url, headers=f_headers)
        else:
            response = requests_type(f_url, headers=f_headers, json=json_data)
    except requests.exceptions.RequestException as e:
        log_to_disk(log_category, lvl='ERROR',
                    msg="RequestsError "+log_key+"="+log_value,
                    kv=kvalue(exception=e))
        log_to_disk(log_category, lvl="ERROR",
                    msg=error_msg+" "+log_key+"="+log_value,
                    kv=kvalue(url=f_url))

    # If we received response, continue
    if response is not None:
        f_dict['results'] = response
        f_dict['status_code'] = f_dict['results'].status_code
        log_to_disk(log_category,
                    msg="HTTPResponse "+log_key+"="+log_value,
                    kv=kvalue(requests_status_code=f_dict['status_code']))

        # Non-HTTP 200 response
        if f_dict['status_code'] >= 400:
            log_to_disk(log_category, lvl="ERROR",
                        msg="RequestsResults "+log_key+"="+log_value,
                        kv=kvalue(requests_content=f_dict['results'].content))
            return False

        # Check for HTTP 2xx response
        if 200 <= f_dict['status_code'] <= 299:
            f_dict['elapsed'] = \
                str(f_dict['results'].elapsed.microseconds)[:-3]

            # Error handling for json in results.content
            try:
                f_dict['json'] = json.loads(f_dict['results'].content)
            except ValueError:
                f_dict['json'] = "{}"

            # Optional development logging: output raw f_dict['json']
            if app_conf['debug'] is True:
                print('JSON_CONTENT:' + str(f_dict['json']))

            log_to_disk(log_category,
                        msg="RequestsResults "+log_key+"="+log_value,
                        kv=kvalue(requests_elapsed_ms=f_dict['elapsed'])
                        )
        #return
        return True

    else:
        # response is None and no exception was caught
        log_to_disk(log_category, lvl="ERROR",
                    msg="requests response is None, no exception caught "+\
                        log_key+"="+log_value,
                    kv=kvalue(url=f_url))
        # return
        return False



def start(app_component="Main"):
    """
    Starts the script
    """
    global t0
    t0 = round(time.time()*1000, 0).__int__()
    log_to_disk('Start', msg=app_name+':'+app_component+' starting invocation', kv=kvalue(t0=t0))


def get_elapsed_ms():
    """
    Returns the elapsed time of the script in ms
    """
    now = round(time.time()*1000, 0).__int__()
    app_elapsed = round(now - t0, 0)
    return app_elapsed


def wrap_up_app(app_component="Main",status="success"):
    """
    Quits the script
    """
    now = round(time.time() * 1000, 0).__int__()

    if status == "success":
        log_lvl = "INFO"
    else:
        log_lvl = "ERROR"

    # Log to disk
    log_to_disk('Finish', lvl=log_lvl,
                msg=app_name+':'+app_component+' ending invocation',
                kv=kvalue(t1=now,
                          status=status,
                          app_elapsed_ms=get_elapsed_ms()))


def quit_app():
    """
    Quits the script
    """
    sys.exit()
