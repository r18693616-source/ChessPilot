import requests
from PIL import Image
from io import BytesIO

# URL for the prediction endpoint
url = "https://vercel-chess-detection.vercel.app/predict"
conf = 0.7


def letterbox_resize(image, target_size):
    """
    Resizes the image to fit within the target_size, maintaining the aspect ratio.
    Adds padding only to one dimension (either top/bottom or left/right) to make the image square.
    """
    orig_w, orig_h = image.size
    scale = min(target_size / orig_w, target_size / orig_h)

    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)

    resized = image.resize((new_w, new_h), Image.LANCZOS)

    # Calculate padding for only one dimension (either top/bottom or left/right)
    x_offset = (target_size - new_w) // 2  # Padding for left/right
    y_offset = (target_size - new_h) // 2  # Padding for top/bottom

    # Create a new square image and paste the resized image onto it
    padded = Image.new("RGB", (target_size, target_size), (0, 0, 0))
    padded.paste(resized, (x_offset, y_offset))

    return padded, x_offset, y_offset, scale


def scale_bbox(detection, x_offset, y_offset, scale):
    """
    Scales the bounding box to the original image size.
    """
    x, y, w, h = detection[:4]
    detection[0] = int((x - x_offset) / scale)
    detection[1] = int((y - y_offset) / scale)
    detection[2] = int((w - x) / scale)
    detection[3] = int((h - y) / scale)
    return detection


def predict(image):
    """
    Makes a prediction using the resized image by sending it to the server.
    Returns the scaled bounding boxes.
    """
    img, x_offset, y_offset, scale = letterbox_resize(image, 640)

    # Convert the image to a byte array wrapped in a BytesIO object
    img_byte_array = BytesIO()
    img.save(img_byte_array, format="JPEG", quality=95)
    img_byte_array.seek(0)  # Reset the stream to the beginning

    # Send the image as a file via POST request
    response = requests.post(url, files={"file": ("resized.png", img_byte_array, "image/jpg")})

    if response.status_code == 200:
        response_json = response.json()
        return [
            scale_bbox(r, x_offset, y_offset, scale) for r in response_json if r[4] > conf
        ]
    else:
        print("Error:", response.status_code)
        return []


def get_positions(image_input):
    """
    Loads an image (from a file path or a PIL Image), makes predictions, and returns the bounding boxes.
    """
    try:
        # Allow image_input to be either a file path (str) or a PIL Image
        if isinstance(image_input, str):
            image = Image.open(image_input)
        else:
            image = image_input
    except Exception as e:
        print(f"Error loading image: {e}")
        return []

    predictions = predict(image)

    if predictions:
        return predictions
    else:
        print("No predictions found.")
        return []


if __name__ == "__main__":
    image_path = "chess-screenshot.png"
    get_positions(image_path)