from PIL import Image

try:
    print("Opening favicon.ico...")
    img = Image.open('favicon.ico')
    
    # Force convert to 32-bit RGBA (True color + Alpha channel)
    img = img.convert('RGBA')
    
    # Windows requires these specific sizes for the icon to scale properly
    # without losing transparency or getting a white background.
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    print("Saving fixed icon as favicon_fixed.ico...")
    img.save('favicon_fixed.ico', format='ICO', sizes=sizes)
    print("Success! You can now use favicon_fixed.ico")
except Exception as e:
    print("Error:", e)
