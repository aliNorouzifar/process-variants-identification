import pm4py
import pandas as pd
from pm4py.objects.log import obj as log_instance



def apply(case_table, event_table, map_info):
    case_table = case_table.rename(columns={map_info['case_id']: 'case:concept:name'})
    event_table = event_table.rename(columns={map_info['case_id']: 'case:concept:name',map_info['activity_name']:'concept:name',map_info['timestamp']:'time:timestamp'})
    log = log_instance.EventLog()
    # case_ids = case_table[map_info['case_id']]
    for index, row in case_table.iterrows():
        trace = log_instance.Trace()
        for i, v in row.items():
            trace.attributes[i]=v
        events = event_table[event_table['case:concept:name']==row['case:concept:name']]
        for index_e, row_e in events.iterrows():
            event = log_instance.Event()
            for ii, vv in row_e.items():
                event[ii] = vv
            trace.append(event)
        log.append(trace)
    return log





