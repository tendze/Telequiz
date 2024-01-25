from cryptography.fernet import Fernet

key = Fernet.generate_key()


def create_key():
    global key
    try:
        file = open('crypto.key', 'a')
        file.close()
        file = open('crypto.key', 'r')
        if len(file.readlines()) == 0:
            file.close()
            file = open('crypto.key', 'wb')
            file.write(key)
        else:
            file.close()
            file = open('crypto.key', 'rb')
            key = file.read()
    except Exception:
        print("Ошибка при генерации ключа шифрования")


create_key()
