from types import SimpleNamespace
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import DashboardStat, Transaction
from django.contrib import messages
from django.shortcuts import render
from django.db.models import Sum
from .models import User, Error, Session, Transaction
from datetime import timedelta
from django.db import connection

def index(request):
    # Get user count  
    user_count = User.objects.count()
    
    # Calculate total revenue from all successful transactions
    total_revenue = Transaction.objects.filter(status='Paid').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # For last 7 days stats:
    date_filter = timezone.now() - timedelta(days=7)
    today_errors = Error.objects.filter(
        created_at__gte=date_filter
    ).count()
    # Get active sessions count (example: sessions created today)
    learned_sessions = Session.objects.filter(
        created_at__date=timezone.now().date()
    ).count()
    
    # Get recent transactions
    recent_transactions = Transaction.objects.order_by('created_at')[:10]

    context = {
        'users': user_count,
        'revenue': total_revenue,
        'errors': today_errors,
        'session': learned_sessions,
        'transactions': recent_transactions,
    }
    
    return render(request, 'main/index.html', context)

def chart_data(request):
    today = timezone.now().date()
    labels = []
    user_data = []
    revenue_data = []

    for i in range(7):
        day = today - timedelta(days=i)
        labels.insert(0, day.strftime("%b %d"))

        user_count = User.objects.filter(created_at__date=day).count()
        revenue_sum = Transaction.objects.filter(
            created_at__date=day, status='Paid'
        ).aggregate(total=Sum('amount'))['total'] or 0

        user_data.insert(0, user_count)
        revenue_data.insert(0, float(revenue_sum))

    return JsonResponse({
        'labels': labels,
        'user_data': user_data,
        'revenue_data': revenue_data,
    })


def add_transaction(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            amount = request.POST.get('amount')
            status = request.POST.get('status')
            
            Transaction.objects.create(
                name=name,
                amount=amount,
                status=status
            )
            
            messages.success(request, 'Transaction added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding transaction: {str(e)}')
        
        return redirect('index')
    
    return redirect('index')

def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        try:
            transaction.name = request.POST.get('name')
            transaction.amount = request.POST.get('amount')
            transaction.status = request.POST.get('status')
            transaction.save()
            
            messages.success(request, 'Transaction updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating transaction: {str(e)}')
        
        return redirect('index')
    
    return redirect('index')

def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        try:
            transaction.delete()
            messages.success(request, 'Transaction deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting transaction: {str(e)}')
        
        return redirect('index')
    
    return redirect('index')