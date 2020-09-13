from django.db import models


class DateInfoMixin(models.Model):
    created = models.DateField('Дата создания', auto_now_add=True)
    updated = models.DateField('Дата изменения', auto_now=True)

    class Meta:
        abstract = True


class Code(models.Model):
    code = models.CharField('Код', max_length=250)


class Client(DateInfoMixin):
    user_id = models.PositiveIntegerField('ID пользователя в Telegram', unique=True)
    name = models.CharField('Имя пользователя', max_length=250)
    phone = models.CharField('Телефон', max_length=20, null=True, blank=True)
    score = models.PositiveIntegerField('Баллы', default=0)

    class Meta:
        verbose_name = 'Пользователь бота'
        verbose_name_plural = 'Пользователи бота'

    def __str__(self):
        return self.name
