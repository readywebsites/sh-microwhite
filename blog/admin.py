from django.contrib import admin
from .models import Blog_Post,Team, Category, Hashtags

# Register your models here.

admin.site.register(Blog_Post)
admin.site.register(Team)
admin.site.register(Category)
admin.site.register(Hashtags)
