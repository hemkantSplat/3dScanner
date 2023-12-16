import sonycam

# Create a connection to your camera
camera = sonycam.Camera()

# Send a command to your camera to take a photo
camera.take_photo()

# Download the photo from your camera
photo = camera.get_photo()

# Save the photo to your computer
photo.save("photo.jpg")
