"""
***************************************************************
* Program Name: main.py
* Author: Daniel Lebedev
* Created : 7/31/2024
***************************************************************
"""
import colorsys
import tkinter
import warnings
from tkinter import filedialog
import Thread
import csv
import numpy
from sklearn.cluster import MiniBatchKMeans
from PIL import Image, ImageDraw, ImageTk, ImageFont


# This increases the max image size limit to supress a pixel count warning
Image.MAX_IMAGE_PIXELS = None  # Disable the limit, or set to a large value like 1e9
warnings.simplefilter('ignore', Image.DecompressionBombWarning)

def ReadCSV():
    threads = []
    try:
        with open('dmc-floss.csv', 'r') as file:
            csvFile = csv.reader(file)
            for row in csvFile:
                if len(row) < 5:
                    continue
                col1, col2, col3, col4, col5 = row
                thread = Thread.Thread(col1, col2, col3, col4, col5)
                threads.append(thread)
    except FileNotFoundError:
        print("CSV file not found.")
    except Exception as e:
        print(f"Error: {e}")
    return threads


def RgbToHex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def RgbToHsv(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def ResizeImage(path, imgX=20, imgY=15, ppi=14):
    try:
        image = Image.open(path)
        width = int(imgX * ppi)
        height = int(imgY * ppi)
        resizedImg = image.resize((width, height), Image.Resampling.LANCZOS)
        return resizedImg
    except IOError:
        print("Error opening or processing image.")
        return None


def ColorDistance(color1, color2):
    return numpy.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))


def FindClosestColor(threads, color, usedColors):
    closestThread = min(threads, key=lambda thread: ColorDistance(thread.color, color))
    return closestThread


def MapColors(finalColors, threads):
    usedColors = set()
    return [FindClosestColor(threads, color, usedColors) for color in finalColors]


def CalculateTxtColor(color):
    r, g, b = color
    if r < 128 and g < 128 and b < 128:
        return "white"
    else:
        return "black"


def SavePixelArtAsPNG(img, threadColors, labels):
    pixelsX, pixelsY = img.size
    scale = 4

    pngImage = Image.new("RGB", (pixelsX * scale, pixelsY * scale))
    draw = ImageDraw.Draw(pngImage)

    for y in range(pixelsY):
        for x in range(pixelsX):
            colorIndex = labels[y, x]
            thread = threadColors[colorIndex]
            left = x * scale
            top = y * scale
            right = left + scale
            bottom = top + scale
            draw.rectangle([left, top, right, bottom], fill=thread.color)
    pngImage.save("pixel_art.png")
    return pngImage


def SaveThreadPng():
    # Open the pixel art image
    pngPath = 'pixel_art.png'
    img = Image.open(pngPath)

    # Define the scale factor for the thread IDs image
    scaleFactor = 64 # Scale factor to enlarge the image

    # Calculate new dimensions
    newWidth = img.width * scaleFactor
    newHeight = img.height * scaleFactor

    # Resize the image
    threadImg = img.resize((newWidth, newHeight), Image.Resampling.NEAREST)

    pixelFont = "Minecraftia-Regular.ttf"

    # Create an ImageDraw object to draw text
    draw = ImageDraw.Draw(threadImg)
    font = ImageFont.truetype(pixelFont, 18)  # Use a TrueType font, adjust size as needed

    # Draw the thread IDs on each pixel
    for y in range(img.height):
        for x in range(img.width):
            colorIndex = labels[y, x]
            thread = threadColors[colorIndex]
            left = x * scaleFactor
            top = y * scaleFactor
            textPosX = left + scaleFactor // 2
            textPosY = top + scaleFactor // 2
            draw.text((textPosX, textPosY), str(thread.id), fill=CalculateTxtColor(thread.color), anchor="mm", font=font)  # Centered text

    # Save the new image as 'thread_ids.png'
    threadImg.save("thread_ids.png")


def DrawPixelArt(img, colorCt, window):
    global pixelArtCanvas, colorKeyCanvas, showThreadVar, pixelsX, pixelsY, scale, currentScale, threadColors, labels
    pixelsX, pixelsY = img.size
    scale = 4

    if img.mode != 'RGB':
        img = img.convert('RGB')

    colors = numpy.array(img).reshape(-1, 3)
    kmeans = MiniBatchKMeans(n_clusters=colorCt)
    kmeans.fit(colors)

    reducedColors = kmeans.cluster_centers_.astype(int)
    finalColors = [tuple(map(int, color)) for color in reducedColors]
    threadColors = MapColors(finalColors, ReadCSV())
    labels = kmeans.labels_.reshape(pixelsY, pixelsX)

    # Create a new image to draw on
    newImg = Image.new('RGB', (pixelsX, pixelsY))
    draw = ImageDraw.Draw(newImg)

    for y in range(pixelsY):
        for x in range(pixelsX):
            colorIndex = labels[y, x]
            thread = threadColors[colorIndex]
            draw.rectangle([x, y, x + 1, y + 1], fill=thread.color)

    # Save the new image as a PNG
    pngPath = 'pixel_art.png'
    newImg.save(pngPath)

    # Call the SaveThreadPng function to create and save the thread IDs image
    SaveThreadPng()

    # Display the saved image on the canvas
    displayImg = Image.open(pngPath)
    displayImg = displayImg.resize((pixelsX * scale, pixelsY * scale), Image.Resampling.NEAREST)
    tkImg = ImageTk.PhotoImage(displayImg)

    # Clear existing widgets
    for widget in frame.winfo_children():
        widget.destroy()

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=0)
    frame.grid_rowconfigure(0, weight=1)

    pixelArtCanvas = tkinter.Canvas(frame, width=600, height=600)
    pixelArtCanvas.grid(row=0, column=0, sticky=tkinter.NSEW)
    pixelArtCanvas.create_image(0, 0, anchor=tkinter.NW, image=tkImg)
    pixelArtCanvas.image = tkImg  # Keep a reference to avoid garbage collection

    colorKeyWidth = 300
    colorKeyHeight = 20 * 30
    colorKeyCanvas = tkinter.Canvas(frame, width=colorKeyWidth, height=colorKeyHeight)
    colorKeyCanvas.grid(row=0, column=1, sticky=tkinter.NS)

    # Draw color key with padding
    padding = 20
    colorKeyX = padding
    colorKeyY = 10
    itemWidth = 50
    itemHeight = 30
    maxItemsPerColumn = 20

    colorKey = list(GetColorKey(threadColors))
    for i, thread in enumerate(colorKey[:100]):
        color = thread.color
        col = i // maxItemsPerColumn
        row = i % maxItemsPerColumn
        xPos = colorKeyX + col * itemWidth
        yPos = colorKeyY + row * itemHeight

        colorKeyCanvas.create_rectangle(
            xPos, yPos, xPos + itemWidth, yPos + itemHeight,
            fill=RgbToHex(color),
            outline=''
        )

        textColor = CalculateTxtColor(color)

        xPos = colorKeyX + col * itemWidth + itemWidth / 2
        yPos = colorKeyY + row * itemHeight + itemHeight / 2

        # Draw the centered text
        colorKeyCanvas.create_text(
            xPos, yPos,
            text=thread.id, fill=textColor,
            anchor=tkinter.CENTER, font=("Helvetica", 8)  # Font size for color key
        )

    pixelArtCanvas.bind("<MouseWheel>", Zoom)
    pixelArtCanvas.bind("<Button-1>", StartPan)
    pixelArtCanvas.bind("<B1-Motion>", Pan)
    pixelArtCanvas.bind("<ButtonRelease-1>", StopPan)

    # Add the checkbox to toggle text
    showThreadVar.set(False)
    threadCheckbox = tkinter.Checkbutton(frame, text="Show Thread IDs", variable=showThreadVar, command=ToggleThreads)
    threadCheckbox.grid(row=1, columnspan=2, pady=(10, 0))


currentScale = 1.0
startX = startY = None


def ToggleThreads():
    global currentScale, pixelArtCanvas, imageX, imageY

    # Calculate the new font size based on currentScale
    fontSize = max(7, int(currentScale / 2))  # Example: Font size scales with currentScale, minimum is 7

    if showThreadVar.get() and currentScale > 8.14:
        # Load the thread IDs image
        threadImg = Image.open('thread_ids.png')
        newWidth = int(pixelsX * scale * currentScale)
        newHeight = int(pixelsY * scale * currentScale)
        threadImg = threadImg.resize((newWidth, newHeight), Image.Resampling.NEAREST)
        tkThreadImg = ImageTk.PhotoImage(threadImg)

        # Overlay the thread IDs image on the pixel art image
        pixelArtCanvas.create_image(imageX, imageY, image=tkThreadImg, anchor=tkinter.NW)
        pixelArtCanvas.thread_image = tkThreadImg  # Keep a reference to avoid garbage collection

    else:
        # Redraw the pixel art image without thread IDs
        pngPath = 'pixel_art.png'
        displayImg = Image.open(pngPath)
        newWidth = int(pixelsX * scale * currentScale)
        newHeight = int(pixelsY * scale * currentScale)
        displayImg = displayImg.resize((newWidth, newHeight), Image.Resampling.NEAREST)
        tkImg = ImageTk.PhotoImage(displayImg)

        pixelArtCanvas.delete("all")
        pixelArtCanvas.create_image(imageX, imageY, image=tkImg, anchor=tkinter.NW)
        pixelArtCanvas.image = tkImg


imageX = imageY = 0


def Zoom(event):
    global currentScale, scale, pixelsX, pixelsY, imageX, imageY
    scaleFactor = 1.2  # Choose a scale factor that maintains quality

    # Calculate new scale based on mouse wheel direction
    if event.delta > 0:  # Scroll up (zoom in)
        newScale = currentScale * scaleFactor
    else:  # Scroll down (zoom out)
        newScale = currentScale / scaleFactor

    # Enforce the scale limits
    if newScale < 0.5:
        newScale = 0.5
    elif newScale > 15.86:
        newScale = 15.86

    # Get the mouse position relative to the canvas
    mouseX = pixelArtCanvas.canvasx(event.x)
    mouseY = pixelArtCanvas.canvasy(event.y)

    # Calculate the image dimensions before resizing
    oldWidth = int(pixelsX * scale * currentScale)
    oldHeight = int(pixelsY * scale * currentScale)

    # Update the current scale
    currentScale = newScale

    # Resize the image
    pngPath = 'pixel_art.png'
    displayImg = Image.open(pngPath)
    newWidth = int(pixelsX * scale * newScale)
    newHeight = int(pixelsY * scale * newScale)
    displayImg = displayImg.resize((newWidth, newHeight), Image.Resampling.NEAREST)
    tkImg = ImageTk.PhotoImage(displayImg)

    # Calculate the new image position to keep the cursor position fixed
    newImageX = mouseX - (mouseX - imageX) * (newWidth / oldWidth)
    newImageY = mouseY - (mouseY - imageY) * (newHeight / oldHeight)

    # Update the image on the canvas
    pixelArtCanvas.delete("all")
    pixelArtCanvas.create_image(newImageX, newImageY, image=tkImg, anchor=tkinter.NW)
    pixelArtCanvas.image = tkImg  # Keep a reference to avoid garbage collection

    # Update the image position
    imageX, imageY = newImageX, newImageY
    # Update text visibility based on new scale
    ToggleThreads()


def StartPan(event):
    global startX, startY
    startX = pixelArtCanvas.canvasx(event.x)
    startY = pixelArtCanvas.canvasy(event.y)


def Pan(event):
    global startX, startY, imageX, imageY
    if startX is None or startY is None:
        return

    # Calculate the amount to move
    dx = pixelArtCanvas.canvasx(event.x) - startX
    dy = pixelArtCanvas.canvasy(event.y) - startY

    # Move the canvas
    pixelArtCanvas.move("all", dx, dy)

    # Update the starting position
    startX = pixelArtCanvas.canvasx(event.x)
    startY = pixelArtCanvas.canvasy(event.y)

    # Update the image position
    imageX += dx
    imageY += dy


def StopPan(event):
    global startX, startY
    startX = startY = None


def LoadImage():
    imgPath = filedialog.askopenfilename()
    if not imgPath:
        return

    ppi = ppiSlider.get()
    width = widthSlider.get()
    height = heightSlider.get()
    colorCt = colorCtSlider.get()

    for widget in frame.winfo_children():
        widget.destroy()

    picture = ResizeImage(imgPath, int(width), int(height), int(ppi))
    if picture:
        DrawPixelArt(picture, colorCt, window)


def GetColorKey(threadColors):
    # Extract the RGB colors from the Thread objects
    sorted_threads = sorted(threadColors, key=lambda thread: RgbToHsv(thread.color)[0])

    # Use a list to maintain order and a set to track seen colors
    seen = set()
    uniqueColors = []

    for thread in sorted_threads:
        color = thread.color
        if color not in seen:
            seen.add(color)
            uniqueColors.append(thread)

    return uniqueColors


def StartGUI():
    global frame, ppiSlider, widthSlider, heightSlider, colorCtSlider, window, pixelArtCanvas, colorKeyCanvas, showThreadVar

    window = tkinter.Tk()
    window.title("Embroidery Pattern Creator")
    windowWidth = 1000
    windowHeight = 700
    window.geometry(f"{windowWidth}x{windowHeight}")

    # Center the window on the screen
    screenWidth = window.winfo_screenwidth()
    screenHeight = window.winfo_screenheight()
    x = (screenWidth // 2) - (windowWidth // 2)
    y = (screenHeight // 2) - (windowHeight // 2)
    window.geometry(f"{windowWidth}x{windowHeight}+{x}+{y}")

    frame = tkinter.Frame(window)
    frame.pack(fill=tkinter.BOTH, expand=True)
    tkinter.Label(frame, text="Select Image File:", font=('Helvetica', 12)).pack(pady=(25, 0))
    imgButton = tkinter.Button(frame, text="Browse", command=LoadImage, width=16, font=('Helvetica', 12))
    imgButton.pack()

    tkinter.Label(frame, text="Thread Count(PPI):", font=('Helvetica', 12)).pack(pady=(25, 0))
    ppiSlider = tkinter.Scale(frame, from_=int(8), to=int(16), orient='horizontal', length=200, width=16, font=('Helvetica', 12))
    ppiSlider.set(14)
    ppiSlider.pack()

    tkinter.Label(frame, text="Number Of Colors:", font=('Helvetica', 12)).pack(pady=(25, 0))
    colorCtSlider = tkinter.Scale(frame, from_=int(2), to=int(100), orient='horizontal', length=200, width=16, font=('Helvetica', 12))
    colorCtSlider.set(24)
    colorCtSlider.pack()

    tkinter.Label(frame, text="Total Width:", font=('Helvetica', 12)).pack(pady=(25, 0))
    widthSlider = tkinter.Scale(frame, from_=int(1), to=int(12), orient='horizontal', length=200, width=16, font=('Helvetica', 12))
    widthSlider.set(4)
    widthSlider.pack()

    tkinter.Label(frame, text="Total Height:", font=('Helvetica', 12)).pack(pady=(25, 0))
    heightSlider = tkinter.Scale(frame, from_=int(1), to=int(12), orient='horizontal', length=200, width=16, font=('Helvetica', 12))
    heightSlider.set(4)
    heightSlider.pack()

    showThreadVar = tkinter.BooleanVar(value=False)

    window.protocol("WM_DELETE_WINDOW", window.destroy)
    window.mainloop()


if __name__ == '__main__':
    StartGUI()
