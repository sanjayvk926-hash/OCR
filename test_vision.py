
from google.cloud import vision

def test_vision():
    client = vision.ImageAnnotatorClient()
    print("Google Cloud Vision API connection successful!")

if __name__ == "__main__":
    test_vision()
