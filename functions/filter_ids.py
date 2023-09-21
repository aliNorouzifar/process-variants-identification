import pm4py
import pandas as pd
from pm4py.objects.log.obj import EventLog

def filter_ids(log,list):
    filtered_log = EventLog([trace for trace in log if trace.attributes['concept:name'] in list])
    return filtered_log


def log_to_tables(log, parameters):
    df = pm4py.convert_to_dataframe(log)
    case_id_name = parameters['case_id']
    timestamp_name = parameters['timestamp']
    acyivity_name = parameters['activity_name']

    # time unit in seconds
    time_unit = 24 * 3600

    output_case_id_name = 'case_id'
    output_timestamp_name = 'timestamp'
    output_acyivity_name = 'activity_name'

    dfunique = df.groupby(by=[case_id_name]).nunique()
    case_attributes = set()
    for col in dfunique.columns:
        if True not in set(dfunique[col] > 1):
            # print(f'{col} can be a case attribute')
            case_attributes.add(col)

    case_table = df[case_attributes.union([case_id_name])].groupby(by=[case_id_name]).first()
    case_table['trace'] = df.groupby(by=[case_id_name])[acyivity_name].apply(lambda x: tuple(list(x.astype(str))))
    case_table['duration'] = df.groupby(by=[case_id_name])[timestamp_name].apply(lambda x: int((x.iloc[-1] - x.iloc[0]).total_seconds() / time_unit))
    case_table = case_table.reset_index()
    case_table = case_table.rename(columns={case_id_name: output_case_id_name})

    non_attributes = {'row_num'}
    event_attributes = set(df.columns) - case_attributes - non_attributes
    event_table = df[event_attributes]
    event_table[timestamp_name] = pd.to_datetime(event_table[timestamp_name], utc=True).dt.strftime('%Y-%m-%d %H:%M:%S')
    event_table = event_table.rename(columns={case_id_name: output_case_id_name, timestamp_name: output_timestamp_name, acyivity_name: output_acyivity_name })

    mapping = {'case_id': output_case_id_name, 'timestamp':output_timestamp_name, 'activity_name':output_acyivity_name}


    return case_table, event_table, mapping