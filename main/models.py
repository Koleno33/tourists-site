from django.db import models
from django.utils import choices
from django.contrib.auth.models import AbstractUser
import datetime

class User(AbstractUser): # наследование от базового класса пользователя AbstractUser, предусмотренного Django
    USER = "user"
    ADMIN = "admin"
    ROLE_CHOICES = { # создание словаря доступных значений для роли
        USER: "Пользователь",
        ADMIN: "Администратор"
    }

    name = models.CharField(max_length=20, default="root") # имя является обязательным для указания при регистрации
                                                           # оставляем значение по умолчанию для автоматического создания
                                                           # суперпользователя Django
    email = models.EmailField(max_length=40) # поле для ввода email с ограничением в 40 символов
    tel = models.CharField(max_length=12, unique=True) # unique=True означает, что поле должно быть уникальным
    birth_date = models.DateField(default=datetime.date.today) # по умолчанию текущая дата, если не указана
    info = models.CharField(max_length=254, blank=True) # blank=True - может быть пустым
    username = models.CharField(max_length=20, unique=True) # логин уникален и имеет длину до 20 символов
    password = models.CharField(max_length=100) # пароль до 100 символов
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ADMIN) # choices содержит словарь возможных значений
    first_name = None # обнуляем поля, предусмотренные Django, которые не нужны согласно ERD приложения
    last_name = None


class Tourist(models.Model):
    # модель туриста имеет отношение 1 к 1 с моделью пользователя
    # on_delete=models.CASCADE означает удаление туриста при удалении пользователя
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Employee(models.Model):
    INSTRUCTOR = "instructor"
    DOCTOR = "doctor"
    VACANCY_CHOICES = {
        INSTRUCTOR: "Инструктор",
        DOCTOR: "Медик"
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employ_date = models.DateField()
    vacancy = models.CharField(max_length=10, choices=VACANCY_CHOICES) 


class Hike(models.Model):
    begin_date = models.DateTimeField()
    end_date = models.DateTimeField()
    name = models.CharField(max_length=100)
    # связь "многие ко многим" с моделью Tourist через промежуточную модель HikeTourist
    tourists = models.ManyToManyField(Tourist, through='HikeTourist')
    # связь "многие ко многим" с моделью Employee (в роли врача) через промежуточную модель HikeDoctor
    doctors = models.ManyToManyField(Employee, through='HikeDoctor', related_name='hikes_as_doctor')
    # связь "многие ко многим" с моделью Employee (в роли инструктора) через промежуточную модель HikeInstructor
    instructors = models.ManyToManyField(Employee, through='HikeInstructor', related_name='hikes_as_instructor')


class HikeTourist(models.Model):
    hike = models.ForeignKey(Hike, on_delete=models.CASCADE)
    tourist = models.ForeignKey(Tourist, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('hike', 'tourist') # пара поход-турист должна быть уникальной


class HikeInstructor(models.Model):
    hike = models.ForeignKey(Hike, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Employee, on_delete=models.CASCADE, limit_choices_to={'vacancy': 'instructor'})
    # Внешний ключ на модель Employee (с ограничением выбора только инструкторов),
    # который удаляет запись при удалении сотрудника

    class Meta:
        unique_together = ('hike', 'instructor')
    

class HikeDoctor(models.Model):
    hike = models.ForeignKey(Hike, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Employee, on_delete=models.CASCADE, limit_choices_to={'vacancy': 'doctor'})

    class Meta:
        unique_together = ('hike', 'doctor')


class Application(models.Model):
    PROCESSING = "processing"
    GOOD = "good"
    BAD = "bad"
    STATUS_CHOICES = {
        PROCESSING: "В обработке",
        GOOD: "Принята",
        BAD: "Отвергнута",
    }

    tourist = models.ForeignKey(Tourist, on_delete=models.CASCADE)
    hike = models.ForeignKey(Hike, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, max_length=10)
    
    def get_status(self):
        # отдельный метод получения текстового представления из STATUS_CHOICES по значению PROCESSING, GOOD или BAD
        return self.STATUS_CHOICES[self.status]

