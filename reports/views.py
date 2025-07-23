from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from datetime import datetime
from receipts.models import Transaction, ExpenseCategory
from django.utils import timezone
from authentication.permissions import IsAdmin,IsEmployee
from receipts.models import Receipt
from django.views.decorators.cache import never_cache
from rest_framework.permissions import AllowAny
from commons.pagination import Pagination
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.conf import settings
from calendar import monthrange
from .models import Report
from authentication.models import Employee
from django.shortcuts import get_object_or_404
@permission_classes([IsAuthenticated])
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def monthly_report_view(request, year, month):
    try:
        year = int(year)
        month = int(month)
        start_date = datetime(year, month, 1)
    except ValueError:
        return Response({"error": "Invalid year or month"}, status=status.HTTP_400_BAD_REQUEST)

    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    # Get all transactions within the date range
    transactions = Transaction.objects.filter(
        receipt__user=request.user,
        
        receipt__date__gte=start_date,
        receipt__date__lte=end_date
    ).select_related('category', 'receipt')
    
    # Spending by category (existing logic)
    spending_by_category = {}
    for category in ExpenseCategory.objects.exclude(name__iexact='Income'):
        total_spent = transactions.filter(category=category).aggregate(Sum('price'))['price__sum'] or 0
        spending_by_category[category.name] = total_spent

        # Save report data
        report, created = Report.objects.get_or_create(
            user=request.user,
            month=start_date.date(),
            category=category,
            defaults={'total_spent': total_spent}
        )
        if not created:
            report.total_spent = total_spent
            report.save()

    # Build expenses list
    expenses = []
    for txn in transactions.order_by('receipt__date', 'id'):
        expenses.append({
            "date": txn.receipt.date.strftime('%Y-%m-%d'),
            "product": txn.item_name,
            "category": txn.category.name if txn.category else None,
            "amount": txn.price
        })

    # Total expenses for the current month
    total_expenses = sum([txn.price for txn in transactions])

    # Previous month expenses for comparison (assuming we can get last month's data)
    previous_month = start_date.replace(month=start_date.month - 1 if start_date.month > 1 else 12, 
                                         year=start_date.year if start_date.month > 1 else start_date.year - 1)
    previous_month_end_date = previous_month.replace(day=monthrange(previous_month.year, previous_month.month)[1], hour=23, minute=59, second=59)

    previous_month_transactions = Transaction.objects.filter(
        receipt__date__gte=previous_month,
        receipt__date__lte=previous_month_end_date
    )
    previous_month_total = sum([txn.price for txn in previous_month_transactions])

    # Calculate percentage change from previous month
    if previous_month_total:
        change_percentage = ((total_expenses - previous_month_total) / previous_month_total) * 100
    else:
        change_percentage = 0

    # Highest spending category
    if spending_by_category:
        highest_category_name = max(spending_by_category, key=spending_by_category.get)
        highest_category_amount = spending_by_category[highest_category_name]
    else:
        highest_category_name = None
        highest_category_amount = 0

    # Calculate average daily spend for the month
    average_daily_spend = total_expenses / last_day if last_day else 0

    # Largest single expense (safe for empty transactions)
    if transactions:
        largest_single_expense = max(transactions, key=lambda x: x.price)
        largest_expense_data = {
            "date": largest_single_expense.receipt.date.strftime('%Y-%m-%d'),
            "product": largest_single_expense.item_name,
            "category": largest_single_expense.category.name if largest_single_expense.category else None,
            "amount": largest_single_expense.price
        }
    else:
        largest_expense_data = "No expenses recorded for this month"

    # Prepare the response data
    response = {
        "month": f"{year}-{month:02d}",
        "total_expenses": total_expenses,
        "previous_month_expenses": previous_month_total,
        "change_from_previous_month": f"{change_percentage:.2f}%",
        "highest_category": {
            "name": highest_category_name,
            "amount": highest_category_amount
        },
        "largest_single_expense": largest_expense_data,
        "spending_by_category": spending_by_category,
        "average_daily_spend": round(average_daily_spend, 2),
        "expenses": expenses
    }

    return Response(response, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([AllowAny])
# @api_view(['GET'])
# @permission_classes([IsAuthenticated, IsAdmin])
def monthly_statistics_view(request):
    now = timezone.now()
    current_year = now.year

    monthly_data = []
    for month in range(1, 13):
        start_date = datetime(current_year, month, 1)
        if month == 12:
            end_date = datetime(current_year + 1, 1, 1)
        else:
            end_date = datetime(current_year, month + 1, 1)

        transactions = Transaction.objects.filter(
            receipt__date__gte=start_date,
            receipt__date__lt=end_date
        )

        expenditure = transactions.aggregate(Sum('price'))['price__sum'] or 0

        monthly_data.append({
            'month': start_date.strftime('%b'),
            'expenditure': expenditure,
        })

    return Response(monthly_data)


from django.conf import settings

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_orders_view(request):
    last_receipt = Receipt.objects.filter(user=request.user).order_by('-id').first()
    if not last_receipt:
        return Response({"message": "No receipts found."}, status=404)

    transactions = Transaction.objects.filter(receipt=last_receipt).select_related('category')

    data = []
    for txn in transactions:
        category_name = txn.category.name
        # Build image URL: assumes images are named as <category_name>.jpg in MEDIA_ROOT/category/
        image_filename = f"{category_name}.jpg"
        image_url = request.build_absolute_uri(f"{settings.MEDIA_URL}category/{image_filename}")
        data.append({
            'item_name': txn.item_name,
            'category': category_name,
            'price': txn.price,
            'category_image': image_url
        })

    return Response({
        "receipt_id": last_receipt.id,
        "shop_name": last_receipt.shop_name,
        "total_amount": last_receipt.total_amount,
        "created_at": last_receipt.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "items": data
    })



@extend_schema(
    parameters=[
        OpenApiParameter("page"),
        OpenApiParameter("size"),
    ],
    responses=None  # You can set a serializer for documentation if you want
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_order_list(request):
    receipts = Receipt.objects.filter(user=request.user).order_by('-id')
    total_elements = receipts.count()

    page = request.query_params.get('page')

    # Pagination
    pagination = Pagination()
    pagination.page = page
    pagination.size = "5"  # Always 5 per page, ignore 'size' param
    receipts = pagination.paginate_data(receipts)

    data = []
    for receipt in receipts:
        # Get all transactions for this receipt
        transactions = Transaction.objects.filter(receipt=receipt).select_related('category')
        # Group by category and sum price
        category_totals = {}
        for txn in transactions:
            cat_name = txn.category.name
            category_totals[cat_name] = category_totals.get(cat_name, 0) + txn.price

        categories = [
            {"name": cat, "amount": amount}
            for cat, amount in category_totals.items()
        ]

        # Build image URL if image exists
        if receipt.image:
            image_url = request.build_absolute_uri(receipt.image.url)
        else:
            image_url = None

        data.append({
            "receipt_id": receipt.id,
            "shop_name": receipt.shop_name,
            "total_amount": receipt.total_amount,
            "created_at": receipt.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "categories": categories,
            "image": image_url
        })

    response = {
        'orders': data,
        'page': pagination.page,
        'size': pagination.size,
        'total_pages': pagination.total_pages,
        'total_elements': total_elements,
    }

    return Response(response, status=status.HTTP_200_OK)

from commons.pagination import Pagination
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@extend_schema(
    parameters=[
        OpenApiParameter("page"),
        OpenApiParameter("size"),
    ],
    responses=None
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_order_product_list(request):
    transactions = Transaction.objects.filter(receipt__user=request.user).select_related('category', 'receipt').order_by('-receipt__created_at')
    total_elements = transactions.count()

    page = request.query_params.get('page')
    pagination = Pagination()
    pagination.page = page
    pagination.size = "5"  # Always 5 per page
    transactions = pagination.paginate_data(transactions)

    data = []
    for txn in transactions:
        category_name = txn.category.name
        image_filename = f"{category_name}.jpg"
        image_url = request.build_absolute_uri(f"{settings.MEDIA_URL}category/{image_filename}")
        data.append({
            "product": txn.item_name,
            "category": category_name,
            "order_date": txn.receipt.created_at.strftime('%Y-%m-%d'),
            "price": txn.price,
            "category_image": image_url
        })

    response = {
        'orders': data,
        'page': pagination.page,
        'size': pagination.size,
        'total_pages': pagination.total_pages,
        'total_elements': total_elements,
    }

    return Response(response, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@never_cache
def daily_category_spending(request):
    # Group by date and category, sum price for each group
    transactions = (
        Transaction.objects
        .filter(receipt__user=request.user)
        .values('receipt__created_at__date', 'category__name')
        .annotate(total=Sum('price'))
        .order_by('-receipt__created_at__date')
    )

    # Organize data by date
    result = {}
    total_spending = 0
    for txn in transactions:
        date = txn['receipt__created_at__date'].strftime('%Y-%m-%d')
        if date not in result:
            result[date] = {
                'total': 0,
                'items': []
            }
        result[date]['items'].append({
            'name': txn['category__name'],
            'amount': txn['total']
        })
        result[date]['total'] += txn['total']
        total_spending += txn['total']

    # Build the response list
    response_list = []
    for date, info in result.items():
        response_list.append({
            'date': date,
            'total': info['total'],
            'items': info['items']
        })

    # Sort by date descending
    response_list.sort(key=lambda x: x['date'], reverse=True)

    return Response({
        'total_spending': total_spending,
        'transactions': response_list
    })
    
from django.db.models import Sum

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsAdmin])
def category_cost_summary(request):
    transactions = Transaction.objects.filter(receipt__user=request.user)
    # Group by category and sum price
    category_totals = (
        transactions
        .values('category__name')
        .annotate(total=Sum('price'))
        .order_by('-total')
    )

    total_spending = transactions.aggregate(total=Sum('price'))['total'] or 0

    highest = category_totals.first()
    lowest = category_totals.last()

    highest_category = {
        "category": highest['category__name'],
        "total": highest['total']
    } if highest else None

    lowest_category = {
        "category": lowest['category__name'],
        "total": lowest['total']
    } if lowest else None

    return Response({
        "total_spending": total_spending,
        "highest_cost_category": highest_category,
        "lowest_cost_category": lowest_category
    })
    
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])  # Admin-only access
def admin_dashboard(request):
    """
    Function-based view to provide access to Admin Dashboard.
    Only accessible by Admin users.
    """
    return Response({"message": "Welcome to the Admin Dashboard!"})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsEmployee])  # Employee-only access
def employee_dashboard(request):
    """
    Function-based view to provide access to Employee Dashboard.
    Only accessible by Employee users.
    """
    return Response({"message": "Welcome to the Employee Dashboard!"})




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsAdmin])
def product_cost_summary(request):
    # Get current date
    current_date = datetime.now()

    # Get the start and end of the current month
    start_date_current_month = datetime(current_date.year, current_date.month, 1)
    end_date_current_month = datetime(current_date.year, current_date.month, monthrange(current_date.year, current_date.month)[1], 23, 59, 59)

    # Get the start and end of the previous month
    start_date_previous_month = datetime(current_date.year, current_date.month - 1 if current_date.month > 1 else 12, 1)
    end_date_previous_month = datetime(current_date.year, current_date.month - 1 if current_date.month > 1 else 12, monthrange(current_date.year, current_date.month - 1 if current_date.month > 1 else 12)[1], 23, 59, 59)

    # Filter transactions for the logged-in user
    all_transactions = Transaction.objects.filter(receipt__user=request.user)

    # Get the highest and lowest cost products across all transactions
    highest_transaction_all_time = all_transactions.order_by('-price').first()
    lowest_transaction_all_time = all_transactions.order_by('price').first()

    highest_cost_all_time = highest_transaction_all_time.price if highest_transaction_all_time else 0
    lowest_cost_all_time = lowest_transaction_all_time.price if lowest_transaction_all_time else 0

    highest_product_all_time = highest_transaction_all_time.item_name if highest_transaction_all_time else "No data"
    lowest_product_all_time = lowest_transaction_all_time.item_name if lowest_transaction_all_time else "No data"

    # Filter transactions for the current month
    transactions_current_month = all_transactions.filter(
        receipt__date__gte=start_date_current_month,
        receipt__date__lte=end_date_current_month
    )

    # Filter transactions for the previous month
    transactions_previous_month = all_transactions.filter(
        receipt__date__gte=start_date_previous_month,
        receipt__date__lte=end_date_previous_month
    )

    # Get the highest and lowest cost products for the current month
    highest_transaction_current_month = transactions_current_month.order_by('-price').first()
    lowest_transaction_current_month = transactions_current_month.order_by('price').first()

    highest_cost_current_month = highest_transaction_current_month.price if highest_transaction_current_month else 0
    lowest_cost_current_month = lowest_transaction_current_month.price if lowest_transaction_current_month else 0

    # Get the highest and lowest cost products for the previous month
    highest_transaction_previous_month = transactions_previous_month.order_by('-price').first()
    lowest_transaction_previous_month = transactions_previous_month.order_by('price').first()

    highest_cost_previous_month = highest_transaction_previous_month.price if highest_transaction_previous_month else 0
    lowest_cost_previous_month = lowest_transaction_previous_month.price if lowest_transaction_previous_month else 0

    # Calculate the percentage change in highest cost product from the previous month to the current month
    if highest_cost_previous_month and highest_cost_previous_month != 0:
        percentage_change_highest = ((highest_cost_current_month - highest_cost_previous_month) / highest_cost_previous_month) * 100
    else:
        percentage_change_highest = 0

    # Calculate the percentage change in lowest cost product from the previous month to the current month
    if lowest_cost_previous_month and lowest_cost_previous_month != 0:
        percentage_change_lowest = ((lowest_cost_current_month - lowest_cost_previous_month) / lowest_cost_previous_month) * 100
    else:
        percentage_change_lowest = 0

    # Format the percentage change to include percentage sign (%) and avoid "+" for increases
    formatted_percentage_change_highest = f"{round(percentage_change_highest, 2)}%" if percentage_change_highest != 0 else "0%"
    formatted_percentage_change_lowest = f"{round(percentage_change_lowest, 2)}%" if percentage_change_lowest != 0 else "0%"

    # Prepare the response data with percentage change included inside the product objects
    response_data = {
        "total_spending": all_transactions.aggregate(total=Sum('price'))['total'] or 0,
        "highest_cost_product_all_time": {
            "product_name": highest_product_all_time,
            "cost": highest_cost_all_time,
            "percentage_change": formatted_percentage_change_highest
        },
        "lowest_cost_product_all_time": {
            "product_name": lowest_product_all_time,
            "cost": lowest_cost_all_time,
            "percentage_change": formatted_percentage_change_lowest
        }
    }

    return Response(response_data, status=200)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@never_cache
def daily_employee_category_spending(request, employee_id):
    # Validate employee existence
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({"message": "Employee not found"}, status=404)

    # Query transactions filtered by employee
    transactions = (
        Transaction.objects
        .filter(employee=employee)
        .values('receipt__created_at__date', 'category__name')
        .annotate(total=Sum('price'))
        .order_by('-receipt__created_at__date')
    )

    # Organize data by date
    result = {}
    total_spending = 0
    for txn in transactions:
        date = txn['receipt__created_at__date'].strftime('%Y-%m-%d')
        if date not in result:
            result[date] = {
                'total': 0,
                'items': []
            }
        result[date]['items'].append({
            'name': txn['category__name'],
            'amount': txn['total']
        })
        result[date]['total'] += txn['total']
        total_spending += txn['total']

    # Build response list sorted by date descending
    response_list = [
        {'date': date, 'total': info['total'], 'items': info['items']}
        for date, info in sorted(result.items(), reverse=True)
    ]

    return Response({
        'employee_id': employee.id,
        'employee_name': employee.full_name,
        'total_spending': total_spending,
        'transactions': response_list
    })
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_orders_by_employee_view(request, employee_id):
    # Validate employee existence
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({"message": "Employee not found."}, status=404)

    # Get last receipt for this employee
    last_receipt = Receipt.objects.filter(employee=employee).order_by('-id').first()
    if not last_receipt:
        return Response({"message": "No receipts found for this employee."}, status=404)

    transactions = Transaction.objects.filter(receipt=last_receipt).select_related('category')

    data = []
    for txn in transactions:
        category_name = txn.category.name if txn.category else "Unknown"
        image_filename = f"{category_name}.jpg"
        image_url = request.build_absolute_uri(f"{settings.MEDIA_URL}category/{image_filename}")
        data.append({
            'item_name': txn.item_name,
            'category': category_name,
            'price': txn.price,
            'category_image': image_url
        })

    return Response({
        "employee_id": employee.id,
        "employee_name": employee.full_name,
        "receipt_id": last_receipt.id,
        "shop_name": last_receipt.shop_name,
        "total_amount": last_receipt.total_amount,
        "created_at": last_receipt.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "items": data
    })
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_order_list_by_id(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    receipts = Receipt.objects.filter(employee=employee).order_by('-id')
    total_elements = receipts.count()

    page = request.query_params.get('page')

    # Assuming your Pagination class works like this:
    pagination = Pagination()
    pagination.page = page
    pagination.size = "5"
    receipts = pagination.paginate_data(receipts)

    data = []
    for receipt in receipts:
        transactions = Transaction.objects.filter(receipt=receipt).select_related('category')

        # Group transactions by category
        category_totals = {}
        for txn in transactions:
            cat_name = txn.category.name
            category_totals[cat_name] = category_totals.get(cat_name, 0) + txn.price

        categories = [{"name": cat, "amount": amount} for cat, amount in category_totals.items()]

        image_url = request.build_absolute_uri(receipt.image.url) if receipt.image else None

        data.append({
            "receipt_id": receipt.id,
            "shop_name": receipt.shop_name,
            "total_amount": receipt.total_amount,
            "created_at": receipt.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "categories": categories,
            "image": image_url
        })

    response = {
        'orders': data,
        'page': pagination.page,
        'size': pagination.size,
        'total_pages': pagination.total_pages,
        'total_elements': total_elements,
    }

    return Response(response, status=status.HTTP_200_OK)
