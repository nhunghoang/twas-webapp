'''
Home page w/ interactive TWAS table. 

Nhung, Jan 2024
'''

import numpy as np 
import pandas as pd 
import os

import dash
from dash import Dash, callback, Input, Output
from dash import html, dcc
from dash import dash_table

import dash_bootstrap_components as dbc

###################################################################

## register this page 
dash.register_page(__name__, name='Neuroimaging TWAS Resource', path='/')

###################################################################

## load TWAS data 
tabl_cols = ['Gene', 'gr-Expression Site', 'Predicted Volume', \
             'TWAS beta', 'TWAS p', 'TWAS p(FDR)', 'TWAS p(Bonf)']

twas_path = os.getcwd() + '/input_data/twas_ukb_volume.csv' 
twas_data = pd.read_csv(twas_path, usecols=tabl_cols) 

sci_kws = {'type': 'numeric', 'format': {'specifier': '.2e'}}
twas_cols = [{'name': c, 'id': c} for c in tabl_cols[:-4]]
twas_cols += [{'name': c, 'id': c, **sci_kws} for c in tabl_cols[-4:]]

## create TWAS table
page_nrow = 20
num_pages = int(twas_data.shape[0] / page_nrow) + 1 
twas_table = dash_table.DataTable(id='twas_table',
                                  columns=twas_cols,

                                  page_current=0,
                                  page_size=page_nrow,
                                  page_action='custom',
                                  page_count=num_pages,

                                  sort_action='custom',
                                  sort_mode='multi',
                                  sort_by=[],
                                  )

######################################################################################

## dropdown menus for filter options
iregs = ['DLPFC', 'Ant. Cingulate', 'Amygdala', 'Hippocampus', \
         'Caudate', 'Putamen', 'Nuc. Accumbens', 'Cerebellum']
genes = np.sort(twas_data['Gene'].unique())
pvals = {'TWAS p': 'p <', 'TWAS p(FDR)': 'p(FDR) <', 'TWAS Bonf': 'p(Bonf) <'}

phen_menu = dcc.Dropdown(iregs, None, id='phen_menu', multi=True)
gmod_menu = dcc.Dropdown(iregs, None, id='gmod_menu', multi=True)
gene_menu = dcc.Dropdown(genes, None, id='gene_menu', multi=True)
pval_menu = dcc.Dropdown(pvals, 'TWAS p', id='pval_menu', multi=False, clearable=False)

## user input for pval filter
pval_input = dcc.Input(id='pval_itxt', type='number', min=0, max=1,
                       debounce=True, value=1, 
                       style={'width': '100%'})

## various text
style_kws = {'display': 'flex', 'align-items': 'center'}
main_text = html.H5('Table Filters', style=style_kws)
gene_text = html.H6('Gene:', style=style_kws)
gmod_text = html.H6('gr-Expression Site:', style=style_kws)
phen_text = html.H6('Predicted Volume:', style=style_kws)
pval_text = html.H6('Statistical Significance:', style=style_kws)

num_res_txt = html.P('', id='num_results_txt', style=style_kws)

######################################################################################

## layout 
kws = {'margin': '10px'}
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Row(main_text, style={'margin': '10px 0px 0px 10px'}),
            dbc.Row(num_res_txt, style={'margin': '0px 0px 10px 10px'}),

            dbc.Row([
                dbc.Col(phen_text, width=5),
                dbc.Col(phen_menu, width=7),
                ], 
                align='center', style={'margin': '10px 0px 20px 10px'}), 

            dbc.Row([
                dbc.Col(gmod_text, width=5),
                dbc.Col(gmod_menu, width=7),
                ], 
                align='center', style={'margin': '10px 0px 20px 10px'}), 

            dbc.Row([
                dbc.Col(gene_text, width=5),
                dbc.Col(gene_menu, width=7),
                ], 
                align='center', style={'margin': '10px 0px 20px 10px'}), 

            dbc.Row([
                dbc.Col(pval_text, width=5),
                dbc.Col(pval_menu, width=4),
                dbc.Col(pval_input, width=3),
                ],
                align='center', style={'margin': '10px 0px 20px 10px'}),
            ],
            width=3),

        dbc.Col([
            dbc.Row(twas_table, style={'margin': '10px 10px 0px 0px'}),
            ],
            width=9),
        ]),
    ],
    fluid=True,
)

######################################################################################

## callbacks 
@callback(
    [Output('twas_table', 'data'),
     Output('twas_table', 'page_count'),
     Output('num_results_txt', 'children')],

    Input('twas_table', 'page_current'),
    Input('twas_table', 'page_size'),
    Input('twas_table', 'sort_by'),

    Input('phen_menu', 'value'),
    Input('gmod_menu', 'value'),
    Input('gene_menu', 'value'),
    Input('pval_menu', 'value'),
    Input('pval_itxt', 'value'),

    )

def update_twas_table(page_current, page_size, sort_by, \
                      phen_filter, gmod_filter, gene_filter, \
                      pval_filter, pval_input):

    df = twas_data

    ## table filters (logical and)
    mask = np.ones(df.shape[0], dtype=bool)
    if phen_filter:
        mask = np.logical_and(mask, df['Predicted Volume'].isin(phen_filter))
    if gmod_filter:
        mask = np.logical_and(mask, df['gr-Expression Site'].isin(gmod_filter))
    if gene_filter:
        mask = np.logical_and(mask, df['Gene'].isin(gene_filter))

    if pval_filter and pval_input:
        mask = np.logical_and(mask, df[pval_filter] < pval_input)

    df = df.loc[mask]
    total_rows = df.shape[0]
    total_rows_text = '{} associations found'.format(total_rows)
    num_pages = int(total_rows / page_size) + 1


    ## sorting
    if len(sort_by):
        cols = [col['column_id'] for col in sort_by]
        ascs = [col['direction'] == 'asc' for col in sort_by]
        df = df.sort_values(cols, ascending=ascs)

    ## paging
    top = page_current * page_size
    bot = (page_current + 1) * page_size

    return df.iloc[top:bot].to_dict('records'), \
           num_pages, total_rows_text



