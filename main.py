# https://hackerthemes.com/bootstrap-cheatsheet/
# https://www.youtube.com/watch?v=0mfIK8zxUds&list=PLh3I780jNsiS3xlk-eLU2dpW3U-wCq4LW
from functions import my_functions, design
import numpy as np
import seaborn as sns
import scipy.signal as sci_sig
from dash import Dash, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import itertools


case_table = pd.DataFrame()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = design.layout()

@app.callback(
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
)
def import_data(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = design.parse_contents(list_of_contents[0], list_of_names[0], list_of_dates[0])
        return children

@app.callback(
    Output(component_id='bar-graph-matplotlib', component_property='src'),
    Output(component_id='bar-graph-matplotlib2', component_property='src'),
    Output(component_id='bar-graph-matplotlib3', component_property='src'),
    Output(component_id='bar-graph-matplotlib4', component_property='src'),
    Input('submit-button','n_clicks'),
    State("my-slider", "value"),
    State("my-slider2", "value"),
    State("my-slider3", "value"),
    Input("TF", "value"),
    State('xaxis-data','value'),
)
def plot_data(n,lag,w, sig, faster, x_data):
    if x_data is not None:
        kpi = x_data
        case_table = pd.read_csv("out.csv")
        case_table = case_table.sort_values(by=[kpi])
        map_range = {}
        for i in range(0, 100, 1):
            map_range[i] = case_table[kpi].iloc[round((i / 100) * len(case_table[kpi]))]
        map_range[100] = case_table[kpi].iloc[len(case_table[kpi]) - 1]

        from pm4py.algo.evaluation.earth_mover_distance import algorithm as emd_evaluator

        num_bins = 100
        bin_size = round(len(case_table) / num_bins)
        point = 0
        bins = []

        i = 0
        while (point + bin_size) <= len(case_table):
            if point + (2 * bin_size) <= len(case_table):
                bins.append(
                    ((min(case_table[point:point + bin_size][kpi]), max(case_table[point:point + bin_size][kpi])), i,
                     case_table[point:point + bin_size]['trace']))
            else:
                bins.append(
                    ((min(case_table[point:][kpi]), max(case_table[point:][kpi])), i, case_table[point:]['trace']))
            point += bin_size
            i += 1

        print('hi')

        stride_q = lag
        dist_vect = [0.0] * 100
        pointer_vec = [i for i in range(0, 100)]

        if faster == True:
            sen = 0.01
        else:
            sen = 0.0001

        windows = [w]
        df = pd.DataFrame([dist_vect] * len(windows), columns=pointer_vec, index=windows)
        for window_q in windows:
            mid = window_q
            print('wait')
            while mid + window_q < 100:
                left = [item for b in bins[mid - window_q:mid] for item in b[2]]
                right = [item for b in bins[mid:mid + window_q] for item in b[2]]
                lang1 = pd.Series(left).value_counts(normalize=True)
                lang1_filt = lang1[lang1 > sen].to_dict()
                lang2 = pd.Series(right).value_counts(normalize=True)
                lang2_filt = lang2[lang2 > sen].to_dict()

                df.loc[window_q][mid] = round(emd_evaluator.apply(lang1_filt, lang2_filt), 2)
                # pointer_vec.append(mid)
                mid += stride_q

        maskx = []
        for x in windows:
            maskx.append([True] * (x) + [False] * (num_bins - 2 * x) + [True] * (x))
        maskx = np.array(maskx)


        fig = plt.figure(figsize=(10, 3))
        sns.histplot(data=case_table, x=kpi, bins=50)
        # fig.suptitle('duration distribution', fontsize=20)
        fig.suptitle(str(kpi) + ' distribution', fontsize=20)
        plt.xlabel('risk score', fontsize=18)
        plt.ylabel('count', fontsize=18)
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)
        # plt.show()

        # Save it to a temporary buffer.
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches = 'tight')
        # Embed the result in the html output.
        fig_data = base64.b64encode(buf.getbuffer()).decode("ascii")
        fig_bar_matplotlib = f'data:image/png;base64,{fig_data}'

        fig2 = plt.figure(figsize=(10, 3))

        # sns.heatmap(np.array(dist_vect,ndmin=2), cmap="Reds", xticklabels=pointer_vec)
        # ax = sns.heatmap(df, cmap="Reds", xticklabels=pointer_vec)
        ax = sns.heatmap(df, cmap="Reds", mask=maskx)
        ax.set_xticks(np.arange(0, 101, 5),
                      labels=[str(x) + "% (" + str(round(map_range[x], 1)) + ")" for x in np.arange(0, 101, 5)])
        # ax.set_facecolor("whitesmoke")
        ax.set_facecolor("gray")
        fig2.suptitle('sliding window analysis', fontsize=20)
        plt.xlabel('traces', fontsize=18)
        plt.ylabel('window size', fontsize=18)
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)
        plt.xticks(rotation=90)
        cbar = ax.collections[0].colorbar
        cbar.ax.tick_params(labelsize=16)
        # Save it to a temporary buffer.
        buf = BytesIO()
        fig2.savefig(buf, format="png", bbox_inches = 'tight')
        # Embed the result in the html output.
        fig_data2 = base64.b64encode(buf.getbuffer()).decode("ascii")
        fig_bar_matplotlib2 = f'data:image/png;base64,{fig_data2}'

        peaks, _ = sci_sig.find_peaks(df.loc[w], height=[sig])
        fig3 = plt.figure(figsize=(10, 3))
        ax = sns.lineplot(
            data=df.loc[w],
            marker='o',  # Style used to mark the join between 2 points
        )
        for xx in peaks:
            # plt.axvline(x=xx, ymin=0, ymax=(df.loc[2][xx]/max(df.loc[2])), linestyle='--',color='r')
            plt.vlines(x=xx, ymin=0, ymax=df.loc[w][xx], linestyle='--', color='r')

        ax.set_xticks(np.arange(0, 101, 5),
                      labels=[str(x) + "% (" + str(round(map_range[x], 2)) + ")" for x in np.arange(0, 101, 5)])
        fig3.suptitle('peaks in EMD', fontsize=20)
        plt.xlabel('traces', fontsize=18)
        plt.ylabel('EMD', fontsize=18)
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)
        plt.xticks(rotation=90)
        buf = BytesIO()
        fig3.savefig(buf, format="png", bbox_inches = 'tight')
        # Embed the result in the html output.
        fig_data3 = base64.b64encode(buf.getbuffer()).decode("ascii")
        fig_bar_matplotlib3 = f'data:image/png;base64,{fig_data3}'



        segments = []
        segments_ids = []
        last_p = 0
        x_state = 0
        for p in peaks:
            new = (x_state, x_state, pd.Series(list(itertools.chain.from_iterable([x[2] for x in bins[last_p:p]]))))
            new_ids = [item for b in bins[last_p:p] for item in b[2].index]
            segments.append(new)
            segments_ids.append(new_ids)
            last_p = p
            x_state += 1
        new = (x_state, x_state, pd.Series(list(itertools.chain.from_iterable([x[2] for x in bins[last_p:]]))))
        new_ids = [item for b in bins[last_p:] for item in b[2].index]
        segments.append(new)
        segments_ids.append(new_ids)

        state = num_bins
        m_dend = []
        cal_list = {}
        itr = 1
        data_points = []
        matrices = []
        labels = []
        mins_vec = []
        state_dic = {}

        if len(segments) >1:
            while len(segments) > 1:
                dist_matrix = np.ones((len(segments), len(segments)))
                for i in range(0, len(segments)):
                    for j in range(i + 1, len(segments)):
                        if (segments[i][0], segments[j][0]) not in cal_list:
                            cal_list[(segments[i][0], segments[j][0])] = my_functions.emd_dist(segments[i], segments[j],sen)
                        dist_matrix[i, j] = cal_list[(segments[i][0], segments[j][0])]
                        data_points.append((itr, dist_matrix[i, j]))
                matrices.append(dist_matrix)
                labels.append([b[1] for b in segments])
                min_dist_ind = np.unravel_index(np.argmin(dist_matrix, axis=None), dist_matrix.shape)
                mins_vec.append(dist_matrix[min_dist_ind])
                m_dend.append([segments[min_dist_ind[0]][1], segments[min_dist_ind[1]][1], dist_matrix[min_dist_ind],
                               len(segments[min_dist_ind[0]][2]) + len(segments[min_dist_ind[1]][2])])
                state_dic[state] = ((segments[min_dist_ind[0]][1], len(segments[min_dist_ind[0]][2])),
                                    (segments[min_dist_ind[1]][1], len(segments[min_dist_ind[1]][2])))
                segments = [segments[k] for k in range(0, len(segments)) if
                            (k != min_dist_ind[0] and k != min_dist_ind[1])] + [((segments[min_dist_ind[0]][0],
                                                                                  segments[min_dist_ind[1]][0]), state,
                                                                                 pd.concat([segments[min_dist_ind[0]][2],
                                                                                            segments[min_dist_ind[1]][2]]))]
                state = state + 1
                itr += 1
                print("hi")

            new = (x_state, x_state, pd.Series(list(itertools.chain.from_iterable([x[2] for x in bins[last_p:]]))))
            new_ids = [item for b in bins[last_p:] for item in b[2].index]
            segments.append(new)
            segments_ids.append(new_ids)

            # fig = plt.figure(figsize=(9, 8))
            ittr = 0

            # order = [labels[ittr].index(i) for i in list_vec[ittr]]

            new_m = matrices[ittr]
            for i in range(0, len(matrices[ittr])):
                for j in range(i, len(matrices[ittr][i])):
                    if i == j:
                        new_m[j, i] = 0
                    else:
                        new_m[j, i] = new_m[i, j]

            cmap = plt.cm.Reds
            fig4 = plt.figure(figsize=(7, 7))
            ax = sns.heatmap(new_m, cmap=cmap, xticklabels=['seg' + str(i) for i in range(1, new_m.shape[0] + 1)],
                             yticklabels=['seg' + str(i) for i in range(1, new_m.shape[0] + 1)])


            fig4.suptitle('segments comparison', fontsize=20)
            plt.xticks(fontsize=16)
            plt.yticks(fontsize=16)
            cbar = ax.collections[0].colorbar
            cbar.ax.tick_params(labelsize=16)
            buf = BytesIO()
            fig4.savefig(buf, format="png", bbox_inches = 'tight')
            # Embed the result in the html output.
            fig_data4 = base64.b64encode(buf.getbuffer()).decode("ascii")
            fig_bar_matplotlib4 = f'data:image/png;base64,{fig_data4}'
        else:
            fig_bar_matplotlib4 = []

    else:
        fig_bar_matplotlib = []
        fig_bar_matplotlib2 = []
        fig_bar_matplotlib3 = []
        fig_bar_matplotlib4 = []
    return fig_bar_matplotlib, fig_bar_matplotlib2, fig_bar_matplotlib3, fig_bar_matplotlib4



if __name__ == '__main__':
    app.run_server(debug=False, port=8002)