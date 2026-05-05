import tempfile

def save_chart_as_image(fig):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.write_image(temp.name, width=800, height=400)
    return temp.name