import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from callbacks import get_categories
import assets.texts as t

tabs_styles = {'border-radius': '4px'}

tab_style = {
    'border-radius': '4px'
}

tab_selected_style = {
    'border-radius': '4px'
}

app_layout = html.Div(
    id='main',
    children=[
        html.A('Astra.Locator',
               id='dash-info-heading-1'),
        html.Div(
            id='main-container',
            children=[
                html.Div(
                    id='dash-info',
                    children=[
                        html.A('Рекомендатор локаций для размещения и продвижения бизнеса',
                               id='dash-info-heading-2'),
                        dcc.Tabs(
                            id="tabs",
                            style=tabs_styles,
                            children=[
                                dcc.Tab(
                                    className='tab-1',
                                    label='Локатор',
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    children=[
                                        dcc.Markdown(t.dashboard_section_text,
                                                     className='dash-info-text'),

                                        html.A('Отрасль:',
                                               id='info-core-dropdown-text'),
                                        dcc.Dropdown(
                                            id='info-core-dropdown',
                                            options=[{'label': x, 'value': x}
                                                     for x in list(get_categories().keys())],
                                            value='Красота',
                                            multi=False
                                        ),

                                        html.A('Виды деятельности:',
                                               id='info-cat-dropdown-text'),
                                        dcc.Dropdown(
                                            id='info-cat-dropdown',
                                            options=[{'label': x, 'value': x}
                                                     for x in get_categories()['Красота']],
                                            value=['Салон красоты', 'Парикмахерская'],
                                            multi=True
                                        ),

                                        html.A('Планируемые часы работы:',
                                               className='info-imp-slider-sub-text'),

                                        dcc.Dropdown(
                                            id='info-hours-dropdown',
                                            options=[{'label': 'Не важно', 'value': 'all'},
                                                     {'label': 'Дневные (8:00-21:59)', 'value': 'day'},
                                                     {'label': 'Ночные (22:00-7:59)', 'value': 'night'},
                                                     ],
                                            value='day',
                                            multi=False
                                        ),

                                        html.A('Что для вас важно?',
                                               className='info-imp-slider-sub-text'),

                                        html.A(['Низкая конкуренция', html.Br(),
                                                '(=мало точек конкурентов в радиусе 0.5 км)'],
                                               className='info-imp-slider-sub-text-l'),
                                        dcc.Slider(
                                            id='info-imp-slider-comps',
                                            className='imp-slider',
                                            min=0,
                                            max=10,
                                            step=1,
                                            value=7
                                        ),

                                        html.A(['Дешевая аренда', html.Br(),
                                                '(=низкая стоимость аренды жилой недвижимости)'],
                                               className='info-imp-slider-sub-text-l'),
                                        dcc.Slider(
                                            id='info-imp-slider-rent',
                                            className='imp-slider',
                                            min=0,
                                            max=10,
                                            step=1,
                                            value=7
                                        ),

                                        html.A(['Высокий траффик', html.Br(),
                                                '(=много людей в среднем в день в радиусе 0.5 км)'],
                                               className='info-imp-slider-sub-text-l'),
                                        dcc.Slider(
                                            id='info-imp-slider-traffic',
                                            className='imp-slider',
                                            min=0,
                                            max=10,
                                            step=1,
                                            value=10

                                        ),

                                        html.A(('В каком радиусе от центра города'
                                                ' рекомендовать локации?'),
                                               className='info-imp-slider-sub-text'),

                                        dcc.Slider(
                                            id='info-imp-slider-dist',
                                            className='imp-slider',
                                            min=0.5,
                                            max=10,
                                            step=0.5,
                                            value=4.5,
                                            marks={km / 10: f'{km / 10} км'
                                                   for km in range(5, 100, 5)}

                                        ),

                                        html.A('Cколько локаций показывать?',
                                               className='info-imp-slider-sub-text'),

                                        dcc.Dropdown(
                                            id='info-top-dropdown',
                                            options=[{'label': 'Все', 'value': 10000},
                                                     {'label': 'Топ-25', 'value': 25},
                                                     {'label': 'Топ-50', 'value': 50},
                                                     {'label': 'Топ-100', 'value': 100},
                                                     {'label': 'Топ-500', 'value': 500},
                                                     {'label': 'Топ-1000', 'value': 1000}],
                                            value=500,
                                            multi=False
                                        )

                                    ]
                                ),
                                dcc.Tab(
                                    className='tab-1',
                                    label='Инструкция',
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    children=[
                                        dcc.Markdown(t.parameters_section_text,
                                                     className='dash-info-text')
                                    ]
                                ),
                                dcc.Tab(
                                    className='tab-1',
                                    label='Данные',
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    children=[
                                        dcc.Markdown(t.data_section_text,
                                                     className='dash-info-text')

                                    ]
                                )
                            ]
                        )
                    ]
                ),

                html.Div(
                    id='dash-map',
                    children=[
                        dcc.Graph(id='map-main')
                    ]
                ),

                html.Div(
                    id='dash-detail',
                    children=[
                        html.A('Топ-10 рекомендованных локаций',
                               className='info-imp-slider-sub-text'),
                        dcc.Textarea(
                            id='detail-api-output',
                            style={'width': '90%',
                                   'height': '90%',
                                   'marginLeft': '40px',
                                   'marginTop': '20px',
                                   },
                        ),
                    ]
                ),

            ]
        )
    ]
)
