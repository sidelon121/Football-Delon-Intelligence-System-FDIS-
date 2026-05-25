print("START")

import plotly.graph_objects as go

print("PLOTLY OK")

fig = go.Figure(
    data=[go.Pie(labels=["A", "B"], values=[10, 20])]
)

print("FIGURE OK")

fig.write_image("test.png")

print("EXPORT SUCCESS")