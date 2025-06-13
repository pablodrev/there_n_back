# There n Back - Logistics Company

## TODO:
1. Добавить в Shipment время прибытия, цену, статус ✅
2. Эндпоинты для Shipment ✅
3. Добавить возможность отзывов ✅
4. Добавить ограничения на CityViewSet для клиента ✅
5. Освобождение водителей и транспорта после выполненной доставки ✅

## Гайд как запустить backend
### 1. Установи [Docker Desktop](https://www.docker.com/)
### 2. Скопируй репозиторий к себе в нужную папочку
```
git clone https://github.com/pablodrev/there_n_back.git --config core.autocrlf=input
```
### 3. Создай виртуальное окружение Python

В терминале перейди в папку backend:
```
cd backend
```
Создай виртуальное окружение:
```
python -m venv .venv
```
Активируй виртуальное окружение:
```
.venv/Scripts/activate
```

### 4. Положи .env файл (кину в тг) в папку atmosphere_crm. В нем все адреса пароли явки
### 5. Запусти Docker контейнеры
В терминале перейди в корневую папку there_n_back:
```
cd ..
```
Собери образы. Тут чуток подождать:
```
docker-compose build
```
Запусти контейнеры:
```
docker-compose up
```
### 6. Если все получилось - ура!
API запускается по адресу [0.0.0.0:8000](0.0.0.0:8000) или [localhost:8000](localhost:8000) (если выдал Page not found 404 значит все работает)

Автоматически сгенерированная документация будет по адресу [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)

## Как зарегистрироваться

### Отправь POST-запрос на адрес [localhost:8000/api/register]()
Пример тела запроса:

```
{
  "email": "user@example.com",
  "username": "string",
  "password": "string",
  "role": "client",
  "first_name": "string",
  "last_name": "string"
}
```

### Если данные валидны, вернется ответ с токеном token. ЭТОТ ТОКЕН НЕ ОГРАНИЧЕН ПО ВРЕМЕНИ, ОН ВЕЧНЫЙ
Пример ответа:
```{
  "token": "9ca0f2fbc3b7c7085dfdcf73dc94d02d5ba32887",
  "user_id": "1a8942d6-b6d4-44ae-bbfe-fec3da3e579b",
  "email": "dispatcher@example.com",
  "username": "dispatcher",
  "role": "dispatcher",
  "first_name": "Bobik",
  "last_name": "Johnes"
}
```

### Токен нужно указывать в каждом последующем запросе в заголовке Authorization
Нужно добавить заголовок Authorization и задать ему значение

Authorization: Token \<token\>

## Как залогиниться

### Отправь POST-запрос на адрес [localhost:8000/api/login]() и в теле укажи email и password

Диспетчер:
```
{
  "email": "dispatcher@example.com",
  "password": "dispatcherpassword"
}
```
Клиент:
```
{
  "email": "client@example.com",
  "password": "clientpassword"
}
```

### Логин в Swagger

Swagger может сам в каждый запрос вставлять этот заголовок Authorization, чтоб не делать этого вручную.


Чтобы залогиниться в Swagger, нажимаешь вверзу справа кнопку Authorize и туда **вставляешь не просто токен, а слово Token и после пробела сам токен.**

То есть не
```
9ca0f2fbc3b7c7085dfdcf73dc94d02d5ba32887
```
а
```
Token 9ca0f2fbc3b7c7085dfdcf73dc94d02d5ba32887
```

И нажимаешь Login