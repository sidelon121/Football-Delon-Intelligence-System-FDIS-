import tempfile

def save_chart_as_image(fig):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.write_image(temp.name) 
    return temp.name
