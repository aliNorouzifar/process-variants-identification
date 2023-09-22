import pm4py
import pandas as pd
from pm4py.objects.log.obj import EventLog
from pm4py.algo.evaluation.earth_mover_distance import algorithm as emd_evaluator
from pm4py.objects.log import obj as log_instance



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

    case_table = df[list(case_attributes.union([case_id_name]))].groupby(by=[case_id_name]).first()
    case_table['trace'] = df.groupby(by=[case_id_name])[acyivity_name].apply(lambda x: tuple(list(x.astype(str))))
    case_table['duration'] = df.groupby(by=[case_id_name])[timestamp_name].apply(lambda x: int((x.iloc[-1] - x.iloc[0]).total_seconds() / time_unit))
    case_table = case_table.reset_index()
    case_table = case_table.rename(columns={case_id_name: output_case_id_name})

    non_attributes = {'row_num'}
    event_attributes = set(df.columns) - case_attributes - non_attributes
    event_table = df[list(event_attributes)]
    event_table[timestamp_name] = pd.to_datetime(event_table[timestamp_name], utc=True)
    if 'EventOrder' in event_table.columns:
        event_table = event_table.sort_values([timestamp_name, 'EventOrder'], ascending=[True, True])
    else:
        event_table = event_table.sort_values([timestamp_name], ascending=[True])
    # event_table[timestamp_name] = pd.to_datetime(event_table[timestamp_name], utc=True).dt.strftime('%Y-%m-%d %H:%M:%S')

    event_table = event_table.rename(columns={case_id_name: output_case_id_name, timestamp_name: output_timestamp_name, acyivity_name: output_acyivity_name })

    mapping = {'case_id': output_case_id_name, 'timestamp':output_timestamp_name, 'activity_name':output_acyivity_name}


    return case_table, event_table, mapping






def tables_to_log(case_table, event_table, map_info):
    case_table = case_table.rename(columns={map_info['case_id']: 'concept:name'})
    event_table = event_table.rename(columns={map_info['case_id']: 'case:concept:name',map_info['activity_name']:'concept:name',map_info['timestamp']:'time:timestamp'})
    event_table['time:timestamp'] = pd.to_datetime(event_table['time:timestamp'], utc=True)
    if 'EventOrder' in event_table.columns:
        event_table = event_table.sort_values(['time:timestamp', 'EventOrder'], ascending=[True, True])
    else:
        event_table = event_table.sort_values(['time:timestamp'], ascending=[True])
    log = log_instance.EventLog()
    # case_ids = case_table[map_info['case_id']]
    for index, row in case_table.iterrows():
        trace = log_instance.Trace()
        for i, v in row.items():
            if not pd.isna(v):
                trace.attributes[i]=v
        events = event_table[event_table['case:concept:name']==row['concept:name']]
        for index_e, row_e in events.iterrows():
            event = log_instance.Event()
            for ii, vv in row_e.items():
                if not pd.isna(vv):
                    event[ii] = vv
            trace.append(event)
        log.append(trace)
    return log

def emd_dist(bin1,bin2,sen):
    lang1 = bin1[2].value_counts(normalize=True)
    lang1_filt = lang1[lang1 > sen].to_dict()
    lang2 = bin2[2].value_counts(normalize=True)
    lang2_filt = lang2[lang2 > sen].to_dict()
    dist = round(emd_evaluator.apply(lang1_filt, lang2_filt), 2)
    return dist

def combine(bin1,bin2,state):
    new_bin = ((bin1[0][0],bin2[0][1]), state, pd.concat([bin1[2],bin2[2]]))
    return(new_bin)

def emd_clustering(bins,ss):
    step1 = {}
    print_ss = {}
    for i,b in enumerate(bins):
        if i<len(bins)-1:
            if (bins[i][0],bins[i+1][0]) not in ss.keys():
                lang1 = bins[i][1].value_counts(normalize=True)
                lang1_filt = lang1[lang1>0.001].to_dict()
                lang2 = bins[i+1][1].value_counts(normalize=True)
                lang2_filt = lang2[lang2>0.001].to_dict()
                # step1[(bins[i][0],bins[i+1][0])] = round(emd_evaluator.apply(lang1_filt, lang2_filt),2)
                step1[(bins[i][0],bins[i+1][0])] = round(emd_evaluator.apply(lang1_filt, lang2_filt),2)
                # print_ss [str(bins[i][0]) + "<-->"+str(bins[i+1][0])] = round(emd_evaluator.apply(lang1_filt, lang2_filt),2)
                print_ss [str(bins[i][0]) + "<-->"+str(bins[i+1][0])] = round(emd_evaluator.apply(lang1_filt, lang2_filt),2)
            else:
                step1[(bins[i][0],bins[i+1][0])] = ss[(bins[i][0],bins[i+1][0])]
                print_ss[str(bins[i][0])+"<-->"+str(bins[i+1][0])] = ss[(bins[i][0],bins[i+1][0])]

    (a,b) = min(step1, key=step1.get)
    print(str(a) + "-><-" + str(b))
    bins_list = [x[0] for x in bins]
    index_a = bins_list.index(a)
    index_b = bins_list.index(b)
    new_bins = bins
    new_bins[index_a] = ((a,b),pd.concat([new_bins[index_a][1],bins[index_b][1]]))
    del new_bins[index_b]
    return new_bins,step1,print_ss


def uncover(coh,perc,inerval):
    if type(coh) != int:
        l1 = coh
        while type(l1) != int:
            l1 = l1[0]
        l2 = coh
        while type(l2) != int:
            l2 = l2[-1]
    else:
        l1 = coh
        l2 = coh

    if l1 != 0:
        first = perc[(l1)*inerval]
    else:
        first = 0
    last = perc[(l2+1) * inerval]


    return first,last




def recursive(case_table,kpi,prc,gam, thr):
    lll = []
    for i in range(0, len(prc),gam):
        left = case_table[case_table[kpi] <= prc[i]]['trace'].value_counts(normalize=True)
        lang_left = left[left > 0.01].to_dict()
        right = case_table[case_table[kpi] > prc[i]]['trace'].value_counts(normalize=True)
        lang_right = right[right > 0.01].to_dict()
        if len(lang_left)!=0 and len(lang_right)!=0:
            lll.append((i,round(emd_evaluator.apply(lang_left, lang_right),2)))
        else:
            lll.append((i,0))
            continue
    lll_sorted = sorted(lll, key= lambda x:x[1])
    m,q = lll_sorted[-1]
    if q >= thr and case_table.shape[0]>200:
        L_left = case_table[case_table[kpi]<=prc[m]]
        prc_left = prc[0:m+1]
        L_right = case_table[case_table[kpi]>prc[m]]
        prc_right = prc[m+1:]
        print(q)
        return (recursive(L_left,kpi,prc_left,gam,thr),recursive(L_right,kpi,prc_right,gam,thr))
    else:
        print(case_table.shape)
        return (case_table[kpi].min(), case_table[kpi].max())
