Поддержано два типа интеграций:
1. Выгружаем в редмайн "полезные" комментарии, которые лежат в гугл-таблице:
```
./useful_comments_saver.py
```
2. Выгружаем в редмайн цепочки комментариев, по которым приходят нотификации:
```
./notification_handler.py
```
3. Создание ответов на комментрии в степике, если у задачи в редмайне есть комментарий и если она имеет статус 'answered'':
```
./comment_creator.py
```


Чтобы все работало, нужно сделать доп настройки:
1. Создать ключи для авторизации на stepik.org

*url:* https://stepik.org/oauth2/applications/register/

*client type:* Confidential

*Authorisation grant type:* client-credentials

Получившиеся `client_id` и `client_secret` необходимо прописать в settings.properties
2. Получить ключ для работы через апи в redmine:

*url:* https://dev.osll.ru/my/account

Справа будет виден api access key, его необходимо прописать в settings.properties, там же можно настроить айди проекта, 
в рамках которого будут создаваться задачи.

3. Для работоспособности скрипта, сохраняющего полезные комментарии нужно еще создать настройки для гугл-апи. 

Можно воспользоваться интсрукцией: https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the_api_name

Получившийся файл нужно переназвать как `client_secret.json` и положить в текущую директорию со скриптами.
