from PIL import Image
import requests
from io import BytesIO

def get_dominant_color(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img = img.resize((50, 50))

    pixels = list(img.getdata())
    avg = tuple(sum(x)/len(pixels) for x in zip(*pixels))
    return f"rgb({int(avg[0])},{int(avg[1])},{int(avg[2])})"
