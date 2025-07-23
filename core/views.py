import boto3
from openai import OpenAI
import json
from django.conf import settings
#
# --- AWS Textract config ---

aws_access_key = settings.AWS_ACCESS_KEY_ID
openai_key = settings.OPENAI_API_KEY
aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
region_name = settings.AWS_REGION

def extract_text_from_local_image(image_path):
    textract_client = boto3.client(
        'textract',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    with open(image_path, 'rb') as img_file:
        img_bytes = img_file.read()

    response = textract_client.detect_document_text(Document={'Bytes': img_bytes})

    lines = [block['Text'] for block in response['Blocks'] if block['BlockType'] == 'LINE']
    return '\n'.join(lines)

def categorize_receipt_with_gpt(extracted_text):
    openai_client = OpenAI(api_key=openai_key)

    prompt = f"""
You are an AI specialized in extracting and categorizing receipt data and fix any text that maybe not well captured and issue like light or scar on recipt etc.
fix the unrelated and and unreadable texts with your knowledge like what it should be. Must Look over the Unit  price and total price correction
if with a item  has a price its total price , then you must look over the total unit over that price and set the unit price according.
Given the following receipt text, extract these fields as JSON:
- date (purchase date like day-month-year format must)
- time (purchase time PM or AM)
- shop_name (if included, if not then title)
- address (shop address, if none give title)
- payment_method (if no method found then cash or otherwise)
- items: a list of objects with fields:
    - name (item name)
    - quantity (number of units)
    - unit_price
    - total_price
    - category (dairy, fruit, vegetable, meat, bakery, beverage, household, other)
- vat (percentage and total_vat; if none then 0)
- tax (percentage and amount; include all taxes, including No Tax.B)
- discount (negative or deductions, if none then 0)
- total_cost (total amount paid)

Receipt text:
\"\"\"{extracted_text}\"\"\"

Return only well-formed JSON. Do not add any explanation or text outside JSON.
"""

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=1500,
    )
    return response.choices[0].message.content

def safe_parse_json(raw_json):
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        return None

if __name__ == "__main__":
    IMAGE_PATH = r"FIVERR_20250510_124802_6767477163049869560_1.jpg"  # Change to your receipt image path
    
    extracted_text = extract_text_from_local_image(IMAGE_PATH)
    
    raw_json = categorize_receipt_with_gpt(extracted_text)
    
    structured_data = safe_parse_json(raw_json)
    if structured_data:
        print(json.dumps(structured_data, indent=4))
    else:
        print("Failed to parse GPT response as JSON.")
