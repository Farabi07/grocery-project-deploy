import os
import sys
import django
import json
import requests
from django.core.files.base import ContentFile
import datetime  # Import datetime for date conversion

# Set up Django environment
sys.path.append('/home/farhad/Desktop/Dream_projects/dream_tousrism_it/')

print("Initializing Django...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'start_project.settings')
django.setup()
print("Django environment setup completed.")

from cms.models import Review


def date_to_milliseconds(date_str):
    """
    Convert date string to milliseconds since Unix epoch.
    """
    try:
        date = datetime.datetime.strptime(date_str, "%B %d, %Y")
        return int(date.timestamp())
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None


def save_review_from_json(review_data):
    supplier = review_data.get('supplier')
    reviewer_name = review_data.get('reviewer_name')
    reviewer_picture_url = review_data.get('image_url')
    # created_at = review_data.get('created_at')
    rating = review_data.get('rating')
    text = review_data.get('text')
    title = review_data.get('title')
    publication = review_data.get('publication')
    url = review_data.get('url')

    # Convert publication date to milliseconds
    publication_ms = date_to_milliseconds(publication)
    if publication_ms is None:
        print(f"Skipping review due to invalid publication date: {publication}")
        return None

    if not reviewer_name or not reviewer_picture_url:
        print("Incomplete review data. Skipping.")
        return None

    response = requests.get(reviewer_picture_url)
    if not response.status_code == 200:
        print(f"Failed to download image from {reviewer_picture_url}. Status code: {response.status_code}")
        return None

    try:
        review_instance = Review.objects.create(
            supplier=supplier,
            reviewer_name=reviewer_name,
            rating=rating,
            # created_at=created_at,
            text=text,
            title=title,
            publication=publication_ms,  # Save publication in milliseconds
            url=url
        )

        # Save image to ImageField
        image_name = f'{reviewer_name}_picture.jpg'
        review_instance.image.save(
            image_name,
            ContentFile(response.content),
            save=True
        )
        print(f"Review '{title}' by {reviewer_name} saved successfully.")
        return review_instance
    except Exception as e:
        print(f"Exception occurred while saving review: {str(e)}")

    return None


def process_reviews_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            reviews_data = json.load(file)
            if isinstance(reviews_data, list):
                for review_data in reviews_data:
                    save_review_from_json(review_data)
            else:
                print("Invalid JSON format. Expecting a list of review objects.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{file_path}': {e}")


# Specify the path to your JSON file
json_file_path = '/home/farhad/Desktop/Dream_projects/dream_tousrism_it/scripts/final.json'
process_reviews_from_file(json_file_path)
