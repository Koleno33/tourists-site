from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Application, HikeInstructor, HikeTourist, User, Tourist, Employee, Hike, HikeDoctor
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import update_session_auth_hash
from django.db import connection
from .forms import (
    RegistrationForm, LoginForm, CustomPasswordChangeForm, 
    ProfileUpdateForm, SQLForm, UserChangeForm, UserIdForm, 
    HikeForm, TouristApplicationForm, HikeIdForm, InstructorApplicationForm
)

def get_user_vacancy(user: User):
    employee = Employee.objects.filter(user=user).first() # type: ignore
    if employee is not None:
        return employee.vacancy
    else:
        return 'tourist'
    
def index(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return render(request, 'profile.html', { 'user': request.user })
        elif request.user.role == 'user':
            vacancy = get_user_vacancy(request.user)
            return render(request, 'profile.html', { 'user': request.user, 'vacancy': vacancy })
    else:
        return render(request, 'index.html')

def info(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return render(request, 'info.html', { 'user': request.user })
        elif request.user.role == 'user':
            vacancy = get_user_vacancy(request.user)
            return render(request, 'info.html', { 'user': request.user, 'vacancy': vacancy })
    else:
        return render(request, 'info.html')

def tourists_view(request):
    if request.user.is_authenticated:
        tourists = Tourist.objects.all()
        return render(request, 'tourists.html', { 'tourists': tourists })
    else:
        return redirect(index)

def staff_view(request):
    if request.user.is_authenticated:
        instructors = Employee.objects.filter(vacancy='instructor')
        doctors = Employee.objects.filter(vacancy='doctor')
        return render(request, 'staff.html', { 'instructors': instructors, 'doctors': doctors })
    else:
        return redirect(index)

def trips(request):
    if request.user.is_authenticated and request.user.role == 'admin':
        hikes = Hike.objects.order_by('id')
        context = {
            'hikes': hikes,
            'columns': [
                'ID', 'Название', 'Дата начала', 'Дата окончания', 
            ]
        }
        return render(request, 'admin_hikes.html', context)
    else:
        if request.user.is_authenticated:
            if get_user_vacancy(request.user) == 'instructor':
                his = HikeInstructor.objects.filter(instructor=request.user.employee)
                hikes = [hi.hike for hi in his]
                return render(request, 'trips.html', {'hikes': hikes})
            elif get_user_vacancy(request.user) == 'doctor':
                his = HikeDoctor.objects.filter(doctor=request.user.employee)
                hikes = [hi.hike for hi in his]
                return render(request, 'trips.html', {'hikes': hikes})
            else:
                hikes = Hike.objects.all()
                for h in hikes:
                    h.is_in = request.user.tourist in h.tourists.all()
                applications = Application.objects.filter(tourist=request.user.tourist)
                return render(request, 'trips.html', {'hikes': hikes, 'applications': applications})
        else:
            hikes = Hike.objects.all()
            return render(request, 'trips.html', {'hikes': hikes})

def change_password(request):
    if not request.user.is_authenticated:
        return redirect(index)
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(index)
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})

def application_view(request):
    if not request.user.is_authenticated or get_user_vacancy(request.user) != 'tourist':
        return redirect(index)
    application = Application(tourist=request.user.tourist)
    if request.method == 'POST':
        form = TouristApplicationForm(request.POST, instance=application)
        if form.is_valid():
            cd = form.cleaned_data
            application.hike = cd['hike']
            application.status = application.PROCESSING
            application.save()
            messages.success(request=request, message="Заявка успешно оформлена")
            return redirect('/trips')
    else:
        form = TouristApplicationForm(instance=application)
    return render(request, 'application.html', {'form': form})

def hikes_applications(request):
    if not request.user.is_authenticated or get_user_vacancy(request.user) != 'instructor':
        return redirect(index)
    if request.method == 'POST':
        formset = [InstructorApplicationForm(request.POST, instance=app, prefix=str(app.id)) for app in Application.objects.filter(hike__instructors=request.user.employee)]
        if all(form.is_valid() for form in formset):
            for form in formset:
                cd = form.cleaned_data
                tourist = form.instance.tourist
                hike = form.instance.hike
                form.save()
                if cd['status'] == Application.GOOD and tourist not in hike.tourists.all():
                    hike.tourists.add(tourist)
                    hike.save()
            messages.success(request=request, message="Данные успешно сохранены")
            return redirect('/trips')
        else:
            messages.error(request=request, message="Данные неверны")
            return redirect('hikes_applications')
    else:
        #formset = [InstructorApplicationForm(request.POST, instance=app, prefix=str(app.id)) for app in Application.objects.all()]
        formset = [InstructorApplicationForm(request.POST, instance=app, prefix=str(app.id)) for app in Application.objects.filter(hike__instructors=request.user.employee)]
    return render(request, 'trips_applications.html', {'formset': formset})

def add_hike(request):
    if not request.user.is_authenticated or get_user_vacancy(request.user) != 'instructor':
        return redirect(index)
    if request.method == 'POST':
        form = HikeForm(request.user.employee, request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            hike = Hike(
                name=cd['name'],
                begin_date=cd['begin_date'],
                end_date=cd['end_date'],
            )
            hike.save()
            hike.tourists.set(cd['tourists'])
            hike.doctors.set(cd['doctors'])
            if 'instructors' in cd:
                hike.instructors.set(cd['instructors'])
            hike.instructors.add(request.user.employee)
            messages.success(request=request, message='Поход успешно добавлен')
            return redirect('/trips')
    else:
        form = HikeForm(current_instructor=request.user.employee)
    return render(request, 'add_hike.html', {'form': form})

def get_change_hike(request):
    if not request.user.is_authenticated or get_user_vacancy(request.user) != 'instructor':
        return redirect(index)
    if request.method == 'POST':
        form = HikeIdForm(request.POST, user=request.user)
        if form.is_valid():
            cd = form.cleaned_data
            hike_id = cd['id']
            return redirect(change_hike, hike_id=hike_id)
    else:
        form = HikeIdForm(user=request.user)
    return render(request, 'hike_id.html', {'form': form})

def change_hike(request, hike_id):
    if not request.user.is_authenticated or get_user_vacancy(request.user) != 'instructor':
        return redirect(index)
    hike = get_object_or_404(Hike, id=hike_id)
    if request.method == 'POST':
        form = HikeForm(request.user.employee, request.POST, instance=hike)
        if form.is_valid():
            cd = form.cleaned_data
            hike.begin_date = cd['begin_date']
            hike.end_date = cd['end_date']
            hike.name = cd['name']
            hike.tourists.set(cd['tourists'])
            hike.doctors.set(cd['doctors'])
            hike.instructors.set([request.user.employee])
            if 'instructors' in cd:
                for instructor in cd['instructors']:
                    if instructor not in hike.instructors.all():
                        hike.instructors.add(instructor)
            hike.save()
            messages.success(request=request, message='Поход успешно изменен')
            return redirect('/trips')
    else:
        form = HikeForm(current_instructor=request.user.employee, instance=hike)
    return render(request, 'change_hike.html', {'form': form})

def change_userdata(request, user_id):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect(index)
    user = get_object_or_404(User, id=user_id)
    if user.role == user.ADMIN:
        role = user.ADMIN
    else:
        role = get_user_vacancy(user)

    if request.method == 'POST':
        form = UserChangeForm(request.POST, user_role=role, instance=user)
        if form.is_valid():
            cd = form.cleaned_data
            user.name = cd['name']
            user.email = cd['email']
            user.tel = cd['tel']
            user.birth_date = cd['birth_date']
            user.info = cd['info']
            user.username = cd['username']
            user.save()
            new_role = cd['role']
            if new_role == user.ADMIN:
                if role == 'tourist':
                    user.tourist.delete()
                elif role in('instructor', 'doctor'):
                    user.employee.delete()
                user.role = user.ADMIN
                user.is_superuser = True
                user.is_staff = True
                user.save()
            elif new_role == 'instructor':
                if role == 'tourist':
                    user.tourist.delete()
                    new_instructor = Employee(
                        user=user,
                        vacancy=Employee.INSTRUCTOR,
                        employ_date=cd['employ_date']
                    )
                    new_instructor.save()
                elif role == 'doctor':
                    user.employee.vacancy = 'instructor'
                    user.employee.save()
                elif role == 'admin':
                    new_instructor = Employee(
                        user=user,
                        vacancy=Employee.INSTRUCTOR,
                        employ_date=cd['employ_date']
                    )
                    new_instructor.save()
                user.role = user.USER
                user.is_superuser = False
                user.is_staff = True
                user.save()
            elif new_role == 'doctor':
                if role == 'tourist':
                    user.tourist.delete()
                    new_doctor= Employee(
                        user=user,
                        vacancy=Employee.DOCTOR,
                        employ_date=cd['employ_date']
                    )
                    new_doctor.save()
                elif role == 'instructor':
                    user.employee.vacancy = 'doctor'
                    user.employee.save()
                elif role == 'admin':
                    new_doctor = Employee(
                        user=user,
                        vacancy=Employee.DOCTOR,
                        employ_date=cd['employ_date']
                    )
                    new_doctor.save()
                    user.role = user.USER
                user.is_superuser = False
                user.is_staff = True
                user.save()
            elif new_role == 'tourist':
                if role in('instructor', 'doctor'):
                    user.employee.delete()
                    new = Tourist(
                        user=user
                    )
                    new.save()
                elif role == 'admin':
                    new_tourist = Tourist(user=user)
                    new_tourist.save()
                    user.role = user.USER
                user.is_superuser = False
                user.is_staff = False 
                user.save()
            if cd['password']:
                user.set_password(cd['password'])
                user.save()
            if new_role in('doctor', 'instructor'):
                user.employee.employ_date = cd['employ_date']
                user.employee.save()
            messages.success(request=request, message='Данные пользователя успешно изменены')
            return redirect(users_view)
    else:
        form = UserChangeForm(user_role=role, instance=user)
    return render(request, 'change_userdata.html', {'form': form})

def profile_update(request):
    if not request.user.is_authenticated:
        return redirect(index)
    if request.method == 'POST':
        if request.user.role == 'admin':
            form = ProfileUpdateForm(request.POST, instance=request.user, is_admin=True) 
        else:
            form = ProfileUpdateForm(request.POST, instance=request.user, is_admin=False) 
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(index)
    else:
        if request.user.role == 'admin':
            form = ProfileUpdateForm(instance=request.user, is_admin=True)
        else:
            form = ProfileUpdateForm(instance=request.user, is_admin=False)
    return render(request, 'profile_update.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect(index)

#def login_view(request):
#    if request.user.is_authenticated:
#        return redirect(index)
#    if request.method == 'POST':
#        form = LoginForm(request.POST)
#        if form.is_valid():
#            cd = form.cleaned_data
#            user = authenticate(username=cd['login'], password=cd['password'])
#            if user is not None:
#                if user.is_active:
#                    login(request, user)
#                    print('login successfully as', user.username)
#                    return redirect(index)
#                else:
#                    messages.error(request, f'Аккаунт {user.username} отключен.')
#                    print('login failed: disabled account ', user.username)
#            else:
#                messages.error(request, 'Неверные данные для входа.')
#                print('login failed: invalid login')
#    else:
#        form = LoginForm()
#    return render(request, 'login.html', { 'form': form })

def user_login(request):
    # Проверяем, аутентифицирован ли пользователь. Если да, перенаправляем на главную страницу.
    if request.user.is_authenticated:
        return redirect(index)

    # Обрабатываем POST-запросы
    if request.method == 'POST':
        # Создаем экземпляр формы с данными из запроса
        form = LoginForm(request.POST)
        # Проверяем, является ли форма валидной
        if form.is_valid():
            # Извлекаем очищенные данные из формы
            cd = form.cleaned_data
            # Аутентифицируем пользователя по имени пользователя и паролю
            user = authenticate(username=cd['login'], password=cd['password'])
            # Проверяем, успешна ли аутентификация
            if user is not None:
                # Проверяем, активен ли аккаунт пользователя
                if user.is_active:
                    # Осуществляем вход пользователя в систему
                    login(request, user)
                    # Перенаправляем пользователя на главную страницу
                    return redirect(index)
                else:
                    # Отправляем сообщение об ошибке, если аккаунт отключен
                    messages.error(request, f'Аккаунт {user.username} отключен.')
            else:
                # Отправляем сообщение об ошибке, если неверны данные для входа
                messages.error(request, 'Неверные данные для входа.')
    else:
        # Если запрос не был методом POST, создаем пустую форму
        form = LoginForm()

    # Передаем контекст с формой в шаблон
    return render(request, 'login.html', {'form': form})

#def register(request):
#    if request.user.is_authenticated:
#        return redirect(index)
#    if request.method == 'POST':
#        form = RegistrationForm(request.POST)
#        if form.is_valid():
#            new_user = User(
#                name=form.cleaned_data['name'],
#                email=form.cleaned_data['email'],
#                tel=form.cleaned_data['tel'],
#                birth_date=form.cleaned_data['birth'],
#                info=form.cleaned_data['info'],
#                username=form.cleaned_data['login'],
#                role=User.USER
#            )
#            new_user.set_password(form.cleaned_data['password'])
#            new_user.save()
#            print('new user added: ', new_user)
#            return render(request, 'success.html')
#    else:
#        form = RegistrationForm()
#
#    context = {
#        'form': form,
#    }
#
#    return render(request, 'register.html', context)

def register(request):
    # Проверяем, аутентифицирован ли пользователь. Если да, перенаправляем на главную страницу
    if request.user.is_authenticated:
        return redirect(index)

    # Обрабатываем POST-запросы.
    if request.method == 'POST':
        # Создаём экземпляр формы с данными из запроса
        form = RegistrationForm(request.POST)
        # Проверяем, является ли форма валидной
        if form.is_valid():
            # Извлекаем очищенные данные из формы
            new_user = User(
                name=form.cleaned_data['name'],  # Имя пользователя
                email=form.cleaned_data['email'],  # Адрес электронной почты
                tel=form.cleaned_data['tel'],  # Номер телефона
                birth_date=form.cleaned_data['birth'],  # Дата рождения
                info=form.cleaned_data['info'],  # Дополнительная информация
                username=form.cleaned_data['login'],  # Логин пользователя
                role=User.USER  # Роль пользователя (по умолчанию "user")
            )
            # Устанавливаем пароль для нового пользователя, используя метод set_password, который автоматически хеширует пароль
            new_user.set_password(form.cleaned_data['password'])
            # Сохраняем нового пользователя в базу данных
            new_user.save()
            # Выводим сообщение в консоль для отладки
            print('new user added: ', new_user)
            # Перенаправляем пользователя на страницу успеха
            return render(request, 'success.html')

    # Если запрос не был методом POST, создаём пустую форму
    else:
        form = RegistrationForm()

    # Передаём контекст с формой в шаблон
    context = {
        'form': form,
    }

    # Отображаем шаблон регистрации с формой.
    return render(request, 'register.html', context)


def fetchall(cursor):
    try:
        # получаем данные
        fetched = cursor.fetchall()
    except:
        # если возникла ошибка - значит данные получить невозможно (результат пустой)
        fetched = []
    return fetched


def query(request):
    if not request.user.is_authenticated or request.user.role != request.user.ADMIN:
        return HttpResponse("Access denied")
    if request.method == 'POST':
        # если передан POST-запрос, то заполняем форму данными из него
        form = SQLForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query'] # получаем текст SQL-запроса, введенный пользователем
            with connection.cursor() as cursor: # создаем курсор для оперирования над данными
                try: # оперирование с данными заключаем в блок try-except, чтобы фиксировать ошибки
                    cursor.execute(query) # выполняем запрос
                    results = fetchall(cursor) # извлекаем значения из курсора
                    context = {
                        'success': True,
                        'results': results,
                        'columns': [col[0] for col in cursor.description] if cursor.description is not None else [],
                        # извлекаем названия столбцов для отображения таблицы в шаблоне
                    }
                    return render(request, 'admin_sql.html', context)
                except Exception as e:
                    # если произошла ошибка при выполнении SQL-запроса, то отправляем текст ошибки пользователю вместе с исходной страницей
                    messages.error(request, e)
                    return render(request, 'admin_sql.html', { 'success': False })
    else:
        # если запрос не POST, то создаем пустую форму
        form = SQLForm()

    # отправляем пользователю страницу и передаем форму
    return render(request, 'admin_sql.html', {'form': form})


def users_view(request):
    if not request.user.is_authenticated or request.user.role != request.user.ADMIN:
        return HttpResponse("Access denied") # type: ignore
    
    admins = User.objects.filter(role=User.ADMIN)

    instructors = Employee.objects.filter(vacancy=Employee.INSTRUCTOR) # type: ignore
    doctors = Employee.objects.filter(vacancy=Employee.DOCTOR) # type: ignore
    tourists = Tourist.objects.all() # type: ignore

    if request.method == 'POST':
        form = UserIdForm(request.POST)
        if form.is_valid():
            user_id=form.cleaned_data['id']
            return redirect(f'/change_userdata/{user_id}')
    else:
        form = UserIdForm()

    context = {
        'admins': admins,
        'instructors': instructors,
        'doctors': doctors,
        'tourists': tourists,
        'form': form,
    }

    return render(request, 'admin_users.html', context)

