from rest_framework import serializers
from .models import Receipt, Transaction
from django_currentuser.middleware import (get_current_authenticated_user, get_current_user)


class TransactionListSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name')  # add category name here
    date = serializers.DateField(source='receipt.date', format='%Y-%m-%d')  # add date from receipt

    class Meta:
        model = Transaction
        fields = [
            'id', 'item_name', 'price', 'category', 'date', 'created_by', 'updated_by'
        ]

    def get_created_by(self, obj):
        return obj.created_by.email if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.email if obj.updated_by else None




class TransactionMinimalListSerializer(serializers.ModelSerializer):
	class Meta:
		model = Transaction
		fields = ['id', 'name']


class TransactionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Transaction
		fields = '__all__'
	
	def create(self, validated_data):
		modelObject = super().create(validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.created_by = user
		modelObject.save()
		return modelObject
	
	def update(self, instance, validated_data):
		modelObject = super().update(instance=instance, validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.updated_by = user
		modelObject.save()
		return modelObject



    
class ReceiptListSerializer(serializers.ModelSerializer):
	created_by = serializers.SerializerMethodField()
	updated_by = serializers.SerializerMethodField()
	class Meta:
		model = Receipt
		fields = '__all__'

	def get_created_by(self, obj):
		return obj.created_by.email if obj.created_by else obj.created_by
		
	def get_updated_by(self, obj):
		return obj.updated_by.email if obj.updated_by else obj.updated_by




class ReceiptMinimalListSerializer(serializers.ModelSerializer):
	class Meta:
		model = Receipt
		fields = ['id', 'name']


class ReceiptSerializer(serializers.ModelSerializer):
	class Meta:
		model = Receipt
		fields = '__all__'
	
	def create(self, validated_data):
		modelObject = super().create(validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.created_by = user
		modelObject.save()
		return modelObject
	
	def update(self, instance, validated_data):
		modelObject = super().update(instance=instance, validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.updated_by = user
		modelObject.save()
		return modelObject



from .models import Receipt, Transaction, ExpenseCategory

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class ReceiptSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True)

    class Meta:
        model = Receipt
        fields = ['user', 'image', 'total_amount', 'date', 'transactions']

