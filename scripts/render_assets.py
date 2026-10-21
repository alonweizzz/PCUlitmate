from pathlib import Path
import cairosvg
from PIL import Image

assets = Path("assets")
for name in ("pcultimate-icon", "pcultimate-logo"):
    cairosvg.svg2png(url=str(assets / f"{name}.svg"), write_to=str(assets / f"{name}.png"),
                     output_width=512 if name.endswith("icon") else 1150)
image = Image.open(assets / "pcultimate-icon.png").convert("RGBA")
image.save(assets / "pcultimate.ico", format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
