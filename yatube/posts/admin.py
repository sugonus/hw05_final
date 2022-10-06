from django.contrib import admin
from .models import Group, Post, Follow

EMPTY = '-пусто-'


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = EMPTY


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Follow)
