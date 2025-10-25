from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os

# Method 1: Pass API key directly to the client
api_key = ""  # Replace with your actual API key
client = genai.Client(api_key=api_key)

# Method 2: Use environment variable (recommended for security)
# Set GOOGLE_API_KEY environment variable before running
# client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

response = client.models.generate_images(
    model='imagen-4.0-generate-001',
    prompt='Robot holding a red skateboard',
    config=types.GenerateImagesConfig(
        number_of_images= 4,
    )
)
for generated_image in response.generated_images:
  generated_image.image.show()