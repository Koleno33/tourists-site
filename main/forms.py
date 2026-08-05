from django import forms
from phonenumber_field.formfields import PhoneNumberField
from datetime import datetime 
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, Hike, Employee, Application, HikeTourist

class RegistrationForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(), max_length=20) # поле для ввода текста длиной 20 символов
    email = forms.EmailField(widget=forms.EmailInput(), max_length=40) # поле для ввода почты длиной 40 символов
    tel = PhoneNumberField(region='RU', max_length=12, # поле для ввода номера телефона из библиотеки phonenumber_field
                           error_messages={
                               "invalid": "Номер должен быть записан в виде: 80123456789 или +70123456789"
                           })
    birth = forms.DateField(widget=forms.DateInput(attrs={'type': "date"}), help_text="Дата рождения") # поле для ввода даты
    info = forms.CharField(widget=forms.TextInput(), required=False, max_length=254) # не обязательное поле информации
    login = forms.CharField(widget=forms.TextInput(), max_length=20) # поле для ввода логина
    password = forms.CharField(widget=forms.PasswordInput(), max_length=100) # поле для ввода пароля с виджетом, скрывающим его
    password2 = forms.CharField(widget=forms.PasswordInput(), max_length=100) # поле для повторного ввода пароля

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs['class'] = "w3-input w3-border" # выставляем классы W3.CSS
        
        self.fields['name'].widget.attrs['type'] = "text" # атрибуты визуализации HTML
        self.fields['name'].widget.attrs['placeholder'] = "Введите имя"

        self.fields['email'].widget.attrs['type'] = "email"
        self.fields['email'].widget.attrs['placeholder'] = "Введите E-mail"

        self.fields['tel'].widget.attrs['type'] = "tel"
        self.fields['tel'].widget.attrs['placeholder'] = "Введите номер телефона"
        self.fields['tel'].widget.attrs['onkeydown'] = "handleKeyDown(event)" # добавляем JS-метод для корректного
                                                                              # ввода номера телефона

        self.fields['birth'].widget.attrs['placeholder'] = "Введите дату рождения"

        self.fields['info'].widget.attrs['type'] = "text"
        self.fields['info'].widget.attrs['placeholder'] = "Перечислите свои навыки, если они есть"

        self.fields['login'].widget.attrs['type'] = "text"
        self.fields['login'].widget.attrs['placeholder'] = "Введите логин"

        self.fields['password'].widget.attrs['type'] = "password"
        self.fields['password'].widget.attrs['placeholder'] = "Введите пароль"

        self.fields['password2'].widget.attrs['type'] = "password"
        self.fields['password2'].widget.attrs['placeholder'] = "Повторите пароль"
    
    def clean_password2(self):
        # функция, активирующаяся при отправке формы и проверяющая поле password2 на совпадение с password
        password1 = self.cleaned_data.get('password') # получаем введенные пароли
        password2 = self.cleaned_data.get('password2')

        if password1 != password2: # пароли не равны
            # отправляем исключение типа forms.ValidationError, чтобы передать пользователю текст ошибки
            raise forms.ValidationError("Введенные пароли должны совпадать")

        return password2

    def clean_birth(self):
        # функция, активирующаяся при отправке формы и проверяющая поле birth на корректность
        birth = self.cleaned_data.get('birth')
        date_now = datetime.now().date() # получаем текущую дату
        if birth is not None and (birth.year < date_now.year - 100 or birth > date_now):
            # дата рождения корректна, если человеу меньше 100 лет и он родился не в будущем
            raise forms.ValidationError("Дата рождения должна быть корректной")
        return birth

    def clean_tel(self):
        # проверка номера телефона
        tel = self.cleaned_data.get('tel')
        if tel is not None: # если номер введен
            if tel.country_code == 7: # если код Российский
                # возвращаем код страны и остальную часть номера единой строкой
                return str(tel.country_code) + str(tel.national_number)
        # если одна из проверка не пройдена, сообщаем текст ошибки пользователю через исключение
        raise forms.ValidationError("Номер должен быть записан в виде: 80123456789 или +70123456789")

    def clean_login(self):
        # функция, активирующаяся при отправке формы и проверяющая поле логина
        if self.cleaned_data.get('login') is None:
            # если логин оказался не введен
            raise forms.ValidationError("Неверно задан логин")
        if ' ' in self.cleaned_data.get('login'):
            # если в логине есть пробелы
            raise forms.ValidationError("Нельзя использовать пробел в логине")
        # ищем пользователей с таким же логином
        user_found = User.objects.filter(username=self.cleaned_data.get('login'))
        if user_found:
            # если пользователь есть - значит логин занят
            raise forms.ValidationError("Пользователь с таким логином уже существует")
        # возвращаем значение логина
        return self.cleaned_data.get('login')


class LoginForm(forms.Form):
    # создаем поле для ввода логина - текстовое поле с виджетом ввода текста и максимальной длиной 20 символов
    login = forms.CharField(widget=forms.TextInput(), max_length=20)
    # создаем поле для ввода логина - текстовое поле с виджетом ввода пароля и максимальной длиной 100 символов
    password = forms.CharField(widget=forms.PasswordInput(), max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) # вызываем конструктор родительского класса forms.Form, передав все аргументы
        
        for field in self.fields.values():
            # проходимся по всем созданным полям для ввода и выставляем классы фреймворка W3 для визуализации
            field.widget.attrs['class'] = "w3-input w3-border"

        # задаем полю вводу логина HTML-атрибуты type и placeholder
        self.fields['login'].widget.attrs['type'] = "text"
        self.fields['login'].widget.attrs['placeholder'] = "Введите логин"

        # задаем полю вводу пароля HTML-атрибуты type и placeholder
        self.fields['password'].widget.attrs['type'] = "password"
        self.fields['password'].widget.attrs['placeholder'] = "Введите пароль"


class ProfileUpdateForm(forms.ModelForm):
    class Meta: 
        model = User
        #fields = ['name', 'email', 'tel', 'birth_date', 'info', 'username', 'password', 'role', 'registered_date']
        fields = ['name', 'email', 'tel', 'birth_date', 'info', 'username']

    def __init__(self, *args, **kwargs):
        is_admin = kwargs.pop('is_admin', False)
        super().__init__(*args, **kwargs)
        if is_admin:
            del self.fields['name']
            del self.fields['email']
            del self.fields['tel']
            del self.fields['birth_date']
            del self.fields['info']


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # добавляем атриюбут HTML placeholder для отображения названия поля ввода
        self.fields["old_password"].widget.attrs['placeholder'] = "Старый пароль"
        self.fields["new_password1"].widget.attrs['placeholder'] = "Новый пароль"
        self.fields["new_password2"].widget.attrs['placeholder'] = "Повторите новый пароль"

        for field in self.fields.values(): # проходим по каждому полю в форме
            field.widget.attrs['class'] = "w3-input w3-border" # выставляем классы W3.CSS
            field.label = None # убираем надпись для заполнения формы, предусмотренную Django


class SQLForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["query"].widget.attrs['class'] = ""

class UserChangeForm(forms.ModelForm):
    class Meta: 
        model = User
        fields = ['name', 'email', 'tel', 'birth_date', 'info', 'username']

    password = forms.CharField(widget=forms.PasswordInput(), max_length=100, required=False)
    employ_date = forms.DateField(widget=forms.DateInput(attrs={'type': "date"}), required=False)
    ROLE_CHOICES = {
        'admin': 'Администратор',
        'tourist': 'Турист',
        'instructor': 'Инструктор',
        'doctor': 'Медик'
    }
    role = forms.ChoiceField(choices=[(key, value) for key, value in ROLE_CHOICES.items()])

    def __init__(self, *args, **kwargs):
        role = kwargs.pop('user_role', 'tourist')
        super().__init__(*args, **kwargs)

        self.fields['tel'] = PhoneNumberField(initial=self.fields['tel'].initial, region='RU', max_length=12, error_messages={ "invalid": "Номер должен быть записан в виде: 80123456789 или +70123456789" })


        self.fields['name'].label = 'Имя'
        self.fields['email'].label = 'E-mail'
        self.fields['tel'].label = 'Номер телефона'
        self.fields['birth_date'].label = 'Дата рождения'
        self.fields['info'].label = 'Информация'
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password'].label = 'Пароль'

        self.fields['role'] = forms.ChoiceField(choices=[(key, value) for key, value in self.ROLE_CHOICES.items()], initial=role)
        self.fields['role'].label = 'Роль'

        if role in (Employee.INSTRUCTOR, Employee.DOCTOR):
            ed = self.instance.employee.employ_date
            self.fields['employ_date'] = forms.DateField(widget=forms.DateInput(attrs={'type': "date"}),
                                                         required=False,
                                                         initial=ed.strftime('%Y-%m-%d'))

        self.fields['employ_date'].label = 'Дата трудоустройства'

    #if role in('admin', 'tourist'):
        #    del self.fields['employ_date']

    def clean(self):
        cleaned_data = super().clean()
        employ_date = cleaned_data.get('employ_date')
        role = self.cleaned_data['role']

        if role in(Employee.INSTRUCTOR, Employee.DOCTOR) and not employ_date:
            raise forms.ValidationError({'employ_date': 'Для персонала дата трудоустройства обязательна'})

        date_now = datetime.now().date()
        if employ_date is not None and (employ_date.year < date_now.year - 100 or employ_date > date_now):
            raise forms.ValidationError("Дата трудоустройства должна быть корректной")

        return cleaned_data 

    def clean_tel(self):
        tel = self.cleaned_data.get('tel')
        if tel is not None:
            if tel.country_code == 7:
                return str(tel.country_code) + str(tel.national_number)
        raise forms.ValidationError("Номер должен быть записан в виде: 80123456789 или +70123456789")


class UserIdForm(forms.Form):
    id = forms.IntegerField(widget=forms.NumberInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['id'].label = 'Введите ID пользователя для изменения его данных'
    
    def clean_id(self):
        try:
            user = User.objects.get(id=self.cleaned_data['id'])
        except:
            raise forms.ValidationError("Пользователь не найден")

        return self.cleaned_data['id']


class HikeForm(forms.ModelForm):
    class Meta: 
        model = Hike
        fields = '__all__'
        widgets = {
            'begin_date': forms.DateTimeInput(attrs={
                'class': 'w3-input w3-border',
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'w3-input w3-border',
            }),
            'name': forms.TextInput(attrs={
                'class': 'w3-input w3-border',
            }),
            'tourists': forms.CheckboxSelectMultiple(attrs={
                'class': 'w3-select w3-border w3-pale-green',
                'size': '5',
            }),
            'doctors': forms.CheckboxSelectMultiple(attrs={
                'class': 'w3-select w3-border w3-pale-green',
                'size': '5',
                'required': False,
            }),
            'instructors': forms.CheckboxSelectMultiple(attrs={
                'class': 'w3-select w3-border w3-pale-green',
                'size': '5',
                'required': False,
            }),
        }


    def __init__(self, current_instructor, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].label = 'Название'
        self.fields['begin_date'].label = 'Дата и время начала'
        self.fields['end_date'].label = 'Дата и время конца'
        self.fields['instructors'].label = 'Выберите инструкторов'
        self.fields['tourists'].label = 'Выберите туристов'
        self.fields['doctors'].label = 'Выберите медиков'

        self.fields['instructors'].label_from_instance = lambda obj: "%s" % f"ID: {obj.user.id}, Имя: {obj.user.username}"
        self.fields['tourists'].label_from_instance = lambda obj: "%s" % f"ID: {obj.user.id}, Имя: {obj.user.username}"
        self.fields['doctors'].label_from_instance = lambda obj: "%s" % f"ID: {obj.user.id}, Имя: {obj.user.username}"

        self.fields['tourists'].required = False
        self.fields['doctors'].required = False
        self.fields['instructors'].required = False

        self.fields['doctors'].queryset = Employee.objects.filter(vacancy='doctor')
        instructors = Employee.objects.filter(vacancy='instructor').exclude(id=current_instructor.id)
        if instructors.exists():
            self.fields['instructors'].queryset = instructors
        else:
            del self.fields['instructors']

class HikeIdForm(forms.Form):
    id = forms.IntegerField(widget=forms.NumberInput())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['id'].label = 'Введите ID похода'
    
    def clean_id(self):
        try:
            if self.user is not None and self.user.role == 'admin':
                hike = Hike.objects.get(id=self.cleaned_data['id'])
            else:
                hike = Hike.objects.get(instructors=self.user.employee, id=self.cleaned_data['id'])
        except Exception as e:
            raise forms.ValidationError("Поход не найден")

        return self.cleaned_data['id']


class TouristApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['hike']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hike'].label_from_instance = lambda obj: "%s" % obj.name
        self.fields['hike'].label = 'Выберите поход'

    def clean_hike(self):
        hikes_ids = [ht.hike.id for ht in HikeTourist.objects.filter(tourist=self.instance.tourist)]
        if self.cleaned_data['hike'].id in hikes_ids:
            raise forms.ValidationError("Вы уже записаны в этот поход")
        hikes_ids = [app.hike.id for app in Application.objects.filter(tourist=self.instance.tourist) if app.status != app.BAD]
        if self.cleaned_data['hike'].id in hikes_ids:
            raise forms.ValidationError("Заявка в этот поход уже на рассмотрении")
        return self.cleaned_data['hike']
       

class InstructorApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].label_from_instance = lambda obj: "%s" % obj.name
        self.fields['status'].label = 'Выберите поход'

