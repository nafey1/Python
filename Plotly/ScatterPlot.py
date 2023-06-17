import numpy as np
import plotly.offline as pyo
import plotly.graph_objects as go

np.random.seed(42)

random_x = np.random.randint(1,101,100)
random_y = np.random.randint(1,101,100)

data   = [go.Scatter(x=random_x, 
                     y=random_y,
                     mode='markers', 
                     marker=dict(
                         size=12,
                         color='rgb(12,321,243)',
                         symbol='pentagon',
                         line ={'width':2}
                     )        
        )]
layout = go.Layout(title= 'My First Scatter Plot!',
                   xaxis= {'title' : 'x-axis data points'},
                   yaxis= {'title' : 'y-axis data points'},
                   hovermode = 'closest')

fig = go.Figure(data=data, layout=layout)
pyo.plot(fig, filename='scatterPlot.html')