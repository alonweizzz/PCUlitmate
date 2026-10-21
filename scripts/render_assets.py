"""Convert branding SVG to PNG/ICO using Windows built-in SVG rendering."""
from pathlib import Path
import subprocess
from PIL import Image

assets = Path("assets").resolve()
ps = r'''
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom.XmlDocument,ContentType=WindowsRuntime] | Out-Null
[Windows.UI.Xaml.Media.Imaging.SvgImageSource,Windows.UI.Xaml,ContentType=WindowsRuntime] | Out-Null
'''
# Windows runners ship ImageMagick; SVG conversion uses its bundled renderer.
for name, width in (("pcultimate-icon", 512), ("pcultimate-logo", 1150)):
    source = assets / (name + ".svg")
    output = assets / (name + ".png")
    subprocess.run(["magick", "-background", "none", "-density", "192",
                    str(source), "-resize", f"{width}x", str(output)], check=True)
icon = Image.open(assets / "pcultimate-icon.png").convert("RGBA")
icon.save(assets / "pcultimate.ico", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
