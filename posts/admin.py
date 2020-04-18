from django.contrib import admin

# из файла models импортируем модель Post
from .models import Post, Group, Comment


class PostAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ("pk", "text", "pub_date", "author")
    # добавляем интерфейс для поиска по тексту постов
    search_fields = ("text",)
    # добавляем возможность фильтрации по дате
    list_filter = ("pub_date",)
    empty_value_display = '-пусто-'  # это свойство сработает для всех колонок: где пусто - там будет эта строка


class GroupAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ("pk", "title", "description")
    # добавляем интерфейс для поиска по тексту
    list_filter = ("title",)
    empty_value_display = '-пусто-'

class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "text")
    list_filter = ("created",)
    empty_value_display = '-пусто-'


# при регистрации модели Post источником конфигурации для неё назначаем класс PostAdmin
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)