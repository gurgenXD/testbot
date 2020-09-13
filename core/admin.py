from django.contrib import admin
from core.models import Client, Code


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'score')


@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'points', 'client')
