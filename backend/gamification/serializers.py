from rest_framework import serializers
from .models import *
class XPEventSerializer(serializers.ModelSerializer): class Meta: model=XPEvent; fields='__all__'
