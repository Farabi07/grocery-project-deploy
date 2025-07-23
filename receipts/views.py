from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Receipt, Transaction, ExpenseCategory
from django.conf import settings
from django.utils import timezone
import requests
from django.db import transaction
from authentication.permissions import IsEmployee, IsAdmin
from reports.models import Report
import json
from core.views import extract_text_from_local_image, categorize_receipt_with_gpt
from authentication.decorators import subscription_required
from django.db.models import F
from authentication.models import Employee
import tempfile
from rest_framework.authentication import SessionAuthentication
from authentication.backends import EmployeeTokenAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.db.models import F
import json
import tempfile
from authentication.models import Employee
from receipts.models import Receipt, ExpenseCategory, Transaction

@api_view(['POST'])
@permission_classes([IsAuthenticated])
# @subscription_required
@parser_classes([MultiPartParser, FormParser])
def receipt_scan_view(request):
    print("FILES RECEIVED:", request.FILES)
    if 'receipt' not in request.FILES:
        return Response({"message": "Receipt file is missing"}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['receipt']

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        for chunk in file.chunks():
            temp_file.write(chunk)
        temp_path = temp_file.name

    try:
        extracted_text = extract_text_from_local_image(temp_path)
        json_output = categorize_receipt_with_gpt(extracted_text)
        ocr_data = json.loads(json_output)
    except Exception as e:
        return Response({"message": f"OCR processing error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not ocr_data:
        return Response({"message": "Error processing receipt data"}, status=status.HTTP_400_BAD_REQUEST)

    total_cost = ocr_data.get('total_cost', 0.0)
    items = ocr_data.get('items', [])
    shop_name = ocr_data.get('shop_name', 'Unknown Shop')  # Extract shop name

    try:
        with transaction.atomic():
            # Save receipt including shop_name
            receipt = Receipt.objects.create(user=request.user, image=file, total_amount=total_cost, shop_name=shop_name)
            category_totals = {}

            for item in items:
                category_name = item.get('category', 'Unknown').capitalize()
                price = item.get('total_price', 0.0)
                item_name = item.get('name', 'Unknown')

                category, _ = ExpenseCategory.objects.get_or_create(name=category_name)
                Transaction.objects.create(
                    user=request.user,
                    receipt=receipt,
                    category=category,
                    item_name=item_name,
                    price=price
                )
                category_totals[category] = category_totals.get(category, 0) + price

            # Update or create report entries per category for the current month
            month_start = timezone.now().date().replace(day=1)
            for category, total_spent in category_totals.items():
                report, created = Report.objects.get_or_create(
                    user=request.user,
                    month=month_start,
                    category=category,
                    defaults={
                        'total_spent': total_spent,
                        'created_by': request.user,
                        'updated_by': request.user
                    }
                )
                if not created:
                    report.total_spent = F('total_spent') + total_spent
                    report.updated_by = request.user
                    report.save()
    except Exception as e:
        return Response({"message": "Database error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Receipt processed successfully"}, status=status.HTTP_201_CREATED)
@api_view(['POST'])
# @authentication_classes([TokenAuthentication, SessionAuthentication])  # or your auth class
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def employee_receipt_scan_view(request, employee_id):
    # 1. Validate employee_id
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({"message": "Invalid employee ID"}, status=status.HTTP_400_BAD_REQUEST)

    if 'receipt' not in request.FILES:
        return Response({"message": "Receipt file is missing"}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['receipt']

    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        for chunk in file.chunks():
            temp_file.write(chunk)
        temp_path = temp_file.name

    try:
        extracted_text = extract_text_from_local_image(temp_path)  # your OCR function
        json_output = categorize_receipt_with_gpt(extracted_text)  # your categorization function
        ocr_data = json.loads(json_output)
    except Exception as e:
        return Response({"message": f"OCR processing error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not ocr_data:
        return Response({"message": "Error processing receipt data"}, status=status.HTTP_400_BAD_REQUEST)

    total_cost = ocr_data.get('total_cost', 0.0)
    items = ocr_data.get('items', [])
    shop_name = ocr_data.get('shop_name', 'Unknown Shop')

    user = request.user

    try:
        with transaction.atomic():
            receipt = Receipt.objects.create(
                user=user,
                employee_id=employee.id,
                image=file,
                total_amount=total_cost,
                shop_name=shop_name,
                created_by=user,
                updated_by=user
            )

            category_totals = {}

            for item in items:
                category_name = item.get('category', 'Unknown').capitalize()
                price = item.get('total_price', 0.0)
                item_name = item.get('name', 'Unknown')

                category, _ = ExpenseCategory.objects.get_or_create(name=category_name)
                Transaction.objects.create(
                    user=user,
                    employee_id=employee.id,
                    receipt=receipt,
                    category=category,
                    item_name=item_name,
                    price=price
                )
                category_totals[category] = category_totals.get(category, 0) + price

            month_start = timezone.now().date().replace(day=1)
            for category, total_spent in category_totals.items():
                report, created = Report.objects.get_or_create(
                    user=user,
                    month=month_start,
                    category=category,
                    defaults={
                        'total_spent': total_spent,
                        'created_by': user,
                        'updated_by': user
                    }
                )
                if not created:
                    report.total_spent = F('total_spent') + total_spent
                    report.updated_by = user
                    report.save()

    except Exception as e:
        return Response({"message": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Receipt processed successfully"}, status=status.HTTP_201_CREATED)