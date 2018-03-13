import os
import subprocess
from itertools import islice
import requests
import urllib.parse
import json
import requests
import pprint

import common
from common.default import *

def obtain_kafka_consumer_groups(bootstrap):
    """
    Obtains the output from this Kafka utility command:
     /opt/broker/bin/kafka-consumer-groups.sh --new-consumer --list

    @retval sorted Python list of kafka consumer groups
    """

    # See app_conf['development'] setting for this
    if app_conf['development'] == True:

        # This is for simulating return data
        decode = 'MongoInserter\n' \
                 'ProductHealthDFAGroup\n' \
                 'syntheticengine_wafpsymsyn03\n' \
                 'MessageExtractor_Perf_SaaS\n' \
                 'ProductHealthConsumerGroup\n' \
                 'syntheticengine_wafpsymsyn01\n' \
                 'HARSplitter\n' \
                 'SyntheticEngine\n' \
                 'DynamicAnomalyEngine2\n' \
                 'syntheticengine_wafpsymsyn02\n'

        split_list = decode.split("\n")

    else:
        # This is the live production execution

        string = None

        try:
            string = subprocess.check_output([
                "/opt/broker/bin/kafka-consumer-groups.sh",
                "--new-consumer",
                "--bootstrap-server",
                bootstrap,
                "--list"
            ])
        except Exception as e:
            print('Unable to grab consumer groups: '+e.__str__())

        if string is not None:
            # Decode, then split by \n into a list
            split_list = string.decode('utf-8').split("\n")
        else:
            return False

    # Whether for dev or for live run,
    # split_list should be available now for further processing

    # Remove any empty strings (e.g. at end of subprocess output)
    group_list = list(filter(None, split_list))
    # Sort list
    sorted_list = sorted(group_list)

    return sorted_list


def obtain_kafka_consumer_lag(bootstrap, consumer_group):
    """
    Obtains the output from this Kafka utility command:
    /opt/broker/bin/kafka-consumer-groups.sh --new-consumer --describe --group

    @retval dictionary of topic:lag for each topic in the consumer_group
    """

    # See app_conf['development'] setting for this
    if app_conf['development'] == True:

        # This is for simulating return data
        decode = 'GROUP                          TOPIC                          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG             OWNER\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5_reload     0          unknown         0               unknown         consumer-4_/10.200.200.112\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5_reload     1          unknown         0               unknown         consumer-4_/10.200.200.112\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5_reload     2          unknown         0               unknown         consumer-4_/10.200.200.112\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5            3          40349111        40349113        2               consumer-3_/10.200.200.112\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5            4          40026469        40026470        1               consumer-3_/10.200.200.112\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5            5          45489131        45489132        1               consumer-3_/10.200.200.112\n' \
                   'MongoInserter                  updatedb                       3          unknown         0               unknown         consumer-1_/10.200.200.113\n' \
                   'MongoInserter                  updatedb                       4          unknown         0               unknown         consumer-1_/10.200.200.113\n' \
                   'MongoInserter                  updatedb                       5          unknown         0               unknown         consumer-1_/10.200.200.113\n' \
                   'MongoInserter                  synth_error                    3          unknown         0               unknown         consumer-2_/10.200.200.112\n' \
                   'MongoInserter                  synth_error                    4          unknown         0               unknown         consumer-2_/10.200.200.112\n' \
                   'MongoInserter                  synth_error                    5          unknown         0               unknown         consumer-2_/10.200.200.112\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5            0          35253984        35253997        13              consumer-3_/10.200.200.113\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5            1          74039511        74039511        0               consumer-3_/10.200.200.113\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5            2          60308560        60308567        7               consumer-3_/10.200.200.113\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5_reload     3          unknown         0               unknown         consumer-4_/10.200.200.113\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5_reload     4          unknown         0               unknown         consumer-4_/10.200.200.113\n' \
                   'MongoInserter                  perf_db_dt_wa_raw_5_reload     5          unknown         0               unknown         consumer-4_/10.200.200.113\n' \
                   'MongoInserter                  synth_error                    0          6932623         6932623         0               consumer-2_/10.200.200.113\n' \
                   'MongoInserter                  synth_error                    1          unknown         0               unknown         consumer-2_/10.200.200.113\n' \
                   'MongoInserter                  synth_error                    2          unknown         0               unknown         consumer-2_/10.200.200.113\n' \
                   'MongoInserter                  updatedb                       0          unknown         0               unknown         consumer-1_/10.200.200.112\n' \
                   'MongoInserter                  updatedb                       1          unknown         0               unknown         consumer-1_/10.200.200.112\n' \
                   'MongoInserter                  updatedb                       2          unknown         0               unknown         consumer-1_/10.200.200.112\n'

        split_list = decode.split("\n")

    else:
        # This is the live production execution

        string = None

        try:
            string = subprocess.check_output([
                "/opt/broker/bin/kafka-consumer-groups.sh",
                "--new-consumer",
                "--bootstrap-server",
                bootstrap,
                "--describe",
                "--group",
                consumer_group
            ])
        except Exception as e:
            print('Unable to grab lag for consumer_group='
                  + consumer_group+' error='+e.__str__())

        if string is None:
            return False
        else:
            decode = string.decode('utf-8')

            if 'does not exist' in decode:
                # Check for:
                # "Consumer group `GROUP_NAME` does not exist or is rebalancing."
                return False
            else:
                # Decode, then split by \n into a list
                split_list = decode.split("\n")

    # Whether for dev or for live run,
    # split_list should be available now for further processing

    # Remove empty '' from the split_list
    group_list = list(filter(None, split_list))

    if len(group_list) < 2:
        #There is only the header line
        return False
    else:

        # Obtain header keys
        header_keys = next(iter(group_list)).split()
        header_keys = [x.lower() for x in header_keys]

        # Skip header line, then create list of key:value pairs
        # for each line
        result = []
        for line in islice(iter(group_list), 1, None):
            result.append(dict(zip(header_keys, line.split())))

        # Compute lag for each topic
        topic_lag = {}
        for line in result:

            # if in Debug, print each individual lag line
            if app_conf['debug'] == True:
                print(line['topic']+" "+line['lag'])

            # Sum up lag by topic
            if line['lag'] == 'unknown':
                donothing = True
            elif line['topic'] not in topic_lag:
                topic_lag[line['topic']] = int(line['lag'])
            else:
                topic_lag[line['topic']] += int(line['lag'])

        return topic_lag


def append_custom_metrics(metric_syntax, metric_key,
                          dimension_type, dimension_value,
                          timestamp, metric_value,
                          dict_metrics):

    # metric_syntax = 'custom:kafka.consumerlag.$metric_key.count'
    # metric_key = 'MongoInserter'
    metric_full_name = metric_syntax.replace('$metric_key', metric_key.lower())
    # dimension_type = 'topic'
    # dimension_value = 'perf_db_dt_wa_raw_5'
    dimension = {}
    dimension[dimension_type] = dimension_value

    data = []
    # timestamp = get_epochms()
    # metric_value = int('0')
    data.append([timestamp, metric_value])

    # metrics = {}
    # metrics['type'] = type
    # metrics['series'] = []

    timeseries_entry = {}
    timeseries_entry['timeseriesId'] = metric_full_name
    timeseries_entry['dimensions'] = dimension
    timeseries_entry['dataPoints'] = data

    dict_metrics['series'].append(timeseries_entry)


def obtain_timeseries_metrics(url_tenant, f_headers,
                              log_category, error_msg,
                              log_key, log_value):

    # timeseries URL
    uri_timeseries = 'api/v1/timeseries'
    f_url = urllib.parse.urljoin(url_tenant, uri_timeseries)

    # Attempt requests
    response = None

    try:
        response = requests.get(f_url, headers=f_headers)
    except requests.exceptions.RequestException as e:
        log_to_disk(log_category, lvl='ERROR',
                    msg="RequestsError "+log_key+"="+log_value,
                    kv=kvalue(exception=e))
        log_to_disk(log_category, lvl="ERROR",
                    msg=error_msg+" "+log_key+"="+log_value,
                    kv=kvalue(url=f_url))

    # If we received response, continue
    if response is not None:
        f_dict = json.loads(response.content.decode('utf-8'))
        return f_dict

def create_kafkalag_metric(url_tenant, f_headers,
                           dt_metrics_list, consumer_group,
                           log_category, error_msg,
                           log_key, log_value):

    # Define metric name with standard convention
    metric_unique = \
        'custom:kafka.consumerlag.' + \
        consumer_group.lower() + \
        '.count'

    # Check if metric already exists
    if metric_unique in [x['timeseriesId'] for x in dt_metrics_list]:
        log_to_disk(log_category,
                    msg="Metric already created at" + \
                        " " + log_key + "=" + log_value,
                    kv=kvalue(status='skip',
                              consumer_group=consumer_group,
                              metric=metric_unique))
        return False
    else:
        # metric does not exist in Dynatrace yet
        # proceed with creating
        definition = '{' \
                 '"displayName" : "Lag - ' + consumer_group + '",' \
                 '"unit" : "Count",' \
                 '"dimensions": [' \
                 '"topic"' \
                 '],' \
                 '"types": [' \
                 '"Kafka"' \
                 ']' \
                 '}'
        json_definition = json.loads(definition)
        # if app_conf['debug'] == True:
        #     if pp:
        #         pp.pprint(json_definition)

        # Create metric endpoint URL
        uri_metric = '/' + metric_unique
        uri_timeseries = 'api/v1/timeseries'
        url_timeseries = urllib.parse.urljoin(url_tenant, uri_timeseries)
        f_url = url_timeseries + uri_metric
        if app_conf['debug'] == True:
            print(f_url)

        # Attempt requests
        response = None

        try:
            response = requests.put(url=f_url, headers=f_headers,
                                    json=json_definition)
        except requests.exceptions.RequestException as e:
            log_to_disk(log_category, lvl='ERROR',
                        msg="RequestsError " + log_key + "=" + log_value,
                        kv=kvalue(exception=e))
            log_to_disk(log_category, lvl="ERROR",
                        msg=error_msg + " " + log_key + "=" + log_value,
                        kv=kvalue(url=url_tenant))
            return False

        # If we received response, continue
        if response is not None:
            log_to_disk(log_category,
                        msg="Metric created successfully" + \
                            " " + log_key + "=" + log_value,
                        kv=kvalue(status='success',
                                  consumer_group=consumer_group,
                                  metric=metric_unique))
            f_dict = json.loads(response.content.decode('utf-8'))
            return f_dict


def push_custom_metrics(url_tenant, f_headers,
                        custom_device, dict_metrics,
                        log_category, error_msg,
                        log_key, log_value):

    # Define destination URL
    f_url = url_tenant + \
            '/api/v1/entity/infrastructure/custom/' + \
            custom_device

    # Load JSON
    json_metrics = json.loads(json.dumps(dict_metrics))

    # See app_conf['development'] setting for this
    if app_conf['development'] == True:
        # Only print, do not attempt to push metrics
        log_to_disk(log_category,
                    msg="Metrics pushed successfully" + \
                        " " + log_key + "=" + log_value,
                    kv=kvalue(status='TESTING',
                              custom_device=custom_device)
                    )
    else:
        # Attempt push of metrics to custom_device

        log_to_disk(log_category,
                    msg="Attempting Push" + \
                        " " + log_key + "=" + log_value,
                    kv=kvalue(custom_device_url=f_url)
                    )

        response = None

        try:
            response = requests.post(url=f_url, headers=f_headers,
                                    json=json_metrics)
        except requests.exceptions.RequestException as e:
            log_to_disk(log_category, lvl='ERROR',
                        msg="RequestsError " + log_key + "=" + log_value,
                        kv=kvalue(exception=e))
            log_to_disk(log_category, lvl="ERROR",
                        msg=error_msg + " " + log_key + "=" + log_value,
                        kv=kvalue(url=url_tenant))
            return False

        # If we received response, continue
        if response is not None:

            requests_content = response.content.decode('utf-8')
            log_to_disk(log_category,
                        msg="Metrics pushed successfully" + \
                            " " + log_key + "=" + log_value,
                        kv=kvalue(status='success',
                                  custom_device=custom_device,
                                  requests_status_code=response.status_code,
                                  requests_content=requests_content)
                        )


def get_epochms(offset_sec="0"):

    offset_ms = int(offset_sec) * 1000
    now_ms = int(round(time.time() * 1000, 0))
    final_time_ms = now_ms - offset_ms
    return final_time_ms


# -----------------------------------   #
#            VARIABLES
#   -----------------------------------   #


# GENERAL VARIABLES
common.default.app_name = "ConsumerLag"
common.default.app_logdir = "log"

# app_name_2017-11-06.log
app_logfile_string = common.default.app_name.lower() + \
                     "_" + str(get_date()) + ".log"

common.default.app_logfile = os.path.join(common.default.app_logdir,
                                          app_logfile_string)


# RUNTIME VARIABLES
conf_file = 'consumerlag.yaml'
app_conf = grab_yaml_from_disk(conf_file)

authentication_list = app_conf['authentication_list']
authentication = authentication_list[0]
headers = authentication['headers']
f_headers = json.loads(headers.replace("'", '"'))

url_tenant = app_conf['url_tenant']
bootstrap = app_conf['bootstrap']
endpoint_custom_device = app_conf['custom_device']
check_metrics_every_x_loops = int(app_conf['check_metrics_every_x_loops'])


# DEV AND DEBUG VARIABLES

# Check for Debug flag, default to False if it is not set in app_conf
if 'debug' in app_conf:
    if app_conf['debug'] is True:
        common.default.app_debug = True
    else:
        common.default.app_debug = False
else:
    common.default.app_debug = False



#   -----------------------------------   #
#            SCRIPT ACTIONS
#   -----------------------------------   #


# Initialize number of loops
num_loops = 0

# Loop indefinitely
while True:

    num_loops += 1

    log_to_disk('Loop',
                msg="Starting",
                kv=kvalue(url_tenant=url_tenant))

    # INITIALIZE METRIC_BUILD VARIABLE

    custom_metric_type = 'Kafka'

    metrics_to_push = {}
    metrics_to_push['type'] = custom_metric_type
    metrics_to_push['series'] = []


    #TODO: Add a heartbeat metric here (and add to dynatrace-validate-timeseries)


    #  Grab Consumer Group List
    log_to_disk('GetConsumerGroups',
                msg="Starting",
                kv=kvalue(bootstrap=bootstrap))

    consumer_group_list = \
        obtain_kafka_consumer_groups(bootstrap=bootstrap)

    log_to_disk('GetConsumerGroups',
                msg="Results",
                kv=kvalue(consumer_group_list=consumer_group_list))

    # If we have run check_metrics_every_x_loops,
    # then we will check for the existence of each metric

    if num_loops == 1 or num_loops % check_metrics_every_x_loops == 0:

        # Grab current list of metrics
        dt_metrics_list = obtain_timeseries_metrics(
            url_tenant=url_tenant,
            f_headers=f_headers,
            log_category='APICall',
            error_msg="unable to obtain metrics list",
            log_key='url_tenant',
            log_value=url_tenant)

        # Iterate through Consumer Groups and create metrics for each one
        for consumer_group in consumer_group_list:
            create_metric_response = create_kafkalag_metric(
                url_tenant=url_tenant,
                f_headers=f_headers,
                dt_metrics_list=dt_metrics_list,
                consumer_group=consumer_group,
                log_category='APICall',
                error_msg="unable to create metric",
                log_key='url_tenant',
                log_value=url_tenant)

    # Continue with processing
    # Grab topics and sum consumer lag by topic
    for consumer_group in consumer_group_list:
        log_to_disk('GetLag',
                    msg="Starting",
                    kv=kvalue(consumer_group=consumer_group))
        consumer_group_lag = \
            obtain_kafka_consumer_lag(bootstrap=bootstrap,
                                      consumer_group=consumer_group)

        log_to_disk('GetLag',
                    msg="Results",
                    kv=kvalue(consumer_group=consumer_group,
                              consumer_group_lag=consumer_group_lag))

        if len(consumer_group_lag) > 0:
            for k, v in consumer_group_lag.items():

                topic_name = k
                topic_value = v

                append_custom_metrics(
                    metric_syntax='custom:kafka.consumerlag.$metric_key.count',
                    metric_key=consumer_group,
                    dimension_type='topic',
                    dimension_value=topic_name,
                    timestamp=get_epochms(),
                    metric_value=topic_value,
                    dict_metrics=metrics_to_push)

    # Debug logging
    log_to_disk('PushMetrics',
                debug=True,
                msg="JSON",
                kv=kvalue(metrics_to_push=metrics_to_push))

    push_custom_metrics(url_tenant=url_tenant,
                        f_headers=f_headers,
                        custom_device=endpoint_custom_device,
                        dict_metrics=metrics_to_push,
                        log_category='APICall',
                        error_msg="unable to push metrics",
                        log_key='url_tenant',
                        log_value=url_tenant
                        )

    log_to_disk('Loop',
                msg="Finished",
                kv=kvalue(url_tenant=url_tenant, num_loops=num_loops))

    if app_conf['development'] == True:
        break

