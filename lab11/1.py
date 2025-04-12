import psycopg2
from psycopg2 import Error
import csv

# Подключение к базе данных
conn = psycopg2.connect(
    database="phonebook",
    user="postgres",
    password="S4j0A2b7",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# Создание функций и процедур в базе данных
def setup_db_functions():
    # Удаляем существующие функции и процедуры
    cur.execute("DROP FUNCTION IF EXISTS search_contacts(text);")
    cur.execute("DROP PROCEDURE IF EXISTS insert_or_update_user(text, text);")
    cur.execute("DROP PROCEDURE IF EXISTS insert_many_users(text[], text[]);")
    cur.execute("DROP FUNCTION IF EXISTS get_paginated_contacts(integer, integer);")
    cur.execute("DROP PROCEDURE IF EXISTS delete_contact_by_name_or_phone(text);")

    # Создаем функции и процедуры с правильными типами данных
    cur.execute(r"""
        CREATE OR REPLACE FUNCTION search_contacts(pattern TEXT)
        RETURNS TABLE(id INT, name VARCHAR(100), phone VARCHAR(20)) AS $$
        BEGIN
            RETURN QUERY
            SELECT * FROM contacts
            WHERE contacts.name ILIKE '%' || pattern || '%'
            OR contacts.phone ILIKE '%' || pattern || '%';
        END;
        $$ LANGUAGE plpgsql;
    """)

    cur.execute(r"""
        CREATE OR REPLACE PROCEDURE insert_or_update_user(p_name TEXT, p_phone TEXT)
        AS $$
        BEGIN
            IF EXISTS (SELECT 1 FROM contacts WHERE phone = p_phone) THEN
                UPDATE contacts 
                SET name = p_name
                WHERE phone = p_phone;
            ELSE
                INSERT INTO contacts (name, phone)
                VALUES (p_name, p_phone);
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cur.execute(r"""
        CREATE OR REPLACE PROCEDURE insert_many_users(names TEXT[], phones TEXT[])
        AS $$
        DECLARE
            i INTEGER;
            invalid_phones TEXT[];
            phone_pattern TEXT := '^\+?[1-9]\d{1,14}$';
        BEGIN
            invalid_phones := ARRAY[]::TEXT[];
            
            FOR i IN 1..array_length(names, 1) LOOP
                IF phones[i] ~ phone_pattern THEN
                    IF NOT EXISTS (SELECT 1 FROM contacts WHERE phone = phones[i]) THEN
                        INSERT INTO contacts (name, phone)
                        VALUES (names[i], phones[i]);
                    END IF;
                ELSE
                    invalid_phones := array_append(invalid_phones, phones[i]);
                END IF;
            END LOOP;
            
            IF array_length(invalid_phones, 1) > 0 THEN
                RAISE NOTICE 'Invalid phone numbers: %', invalid_phones;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cur.execute(r"""
        CREATE OR REPLACE FUNCTION get_paginated_contacts(p_limit INT, p_offset INT)
        RETURNS TABLE(id INT, name VARCHAR(100), phone VARCHAR(20)) AS $$
        BEGIN
            RETURN QUERY
            SELECT * FROM contacts
            ORDER BY id
            LIMIT p_limit OFFSET p_offset;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cur.execute(r"""
        CREATE OR REPLACE PROCEDURE delete_contact_by_name_or_phone(search_value TEXT)
        AS $$
        BEGIN
            DELETE FROM contacts 
            WHERE name = search_value OR phone = search_value;
        END;
        $$ LANGUAGE plpgsql;
    """)

    conn.commit()

# Функция для поиска по шаблону
def search_by_pattern():
    pattern = input("Введите шаблон для поиска (имя или телефон): ")
    cur.execute("SELECT * FROM search_contacts(%s)", (pattern,))
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Имя: {row[1]}, Телефон: {row[2]}")

# Добавление или обновление одного контакта
def insert_or_update_contact():
    name = input("Введите имя: ")
    phone = input("Введите номер телефона: ")
    cur.execute("CALL insert_or_update_user(%s, %s)", (name, phone))
    conn.commit()
    print("Контакт обработан.")

# Добавление нескольких контактов вручную
def insert_multiple_manually():
    try:
        num = int(input("Сколько контактов вы хотите добавить? "))
        names = []
        phones = []
        for _ in range(num):
            name = input("Введите имя: ")
            phone = input("Введите номер телефона: ")
            names.append(name)
            phones.append(phone)
        cur.execute("CALL insert_many_users(%s, %s)", (names, phones))
        conn.commit()
        print("Контакты обработаны. Проверьте, есть ли некорректные номера телефонов.")
    except ValueError:
        print("Некорректное число. Пожалуйста, введите целое число.")
    except Error as e:
        print(f"Ошибка базы данных: {e}")
        conn.rollback()

# Запрос с пагинацией
def query_paginated():
    limit = int(input("Введите лимит: "))
    offset = int(input("Введите смещение: "))
    cur.execute("SELECT * FROM get_paginated_contacts(%s, %s)", (limit, offset))
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Имя: {row[1]}, Телефон: {row[2]}")

# Удаление по имени или телефону
def delete_by_name_or_phone():
    value = input("Введите имя или телефон для удаления: ")
    cur.execute("CALL delete_contact_by_name_or_phone(%s)", (value,))
    conn.commit()
    print("Контакт удален.")

# Вставка из CSV
def insert_from_csv(file_path):
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (row[0], row[1]))
    conn.commit()
    print("Данные из CSV успешно добавлены.")

# Добавление контакта вручную
def insert_from_input():
    name = input("Введите имя: ")
    phone = input("Введите номер телефона: ")
    cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (name, phone))
    conn.commit()
    print("Новый контакт добавлен.")

# Обновление контакта
def update_contact():
    contact_id = input("Введите ID для обновления: ")
    new_name = input("Введите новое имя: ")
    new_phone = input("Введите новый телефон: ")
    cur.execute("UPDATE contacts SET name = %s, phone = %s WHERE id = %s", (new_name, new_phone, contact_id))
    conn.commit()
    print("Контакт обновлен.")

# Удаление контакта по ID
def delete_contact():
    contact_id = input("Введите ID для удаления: ")
    cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
    conn.commit()
    print("Контакт удален.")

# Удаление всех контактов
def delete_all_contacts():
    cur.execute("TRUNCATE TABLE contacts RESTART IDENTITY CASCADE;")
    conn.commit()
    print("Все контакты удалены.")

# Показать все контакты
def show_all_contacts():
    cur.execute("SELECT * FROM contacts")
    rows = cur.fetchall()
    if rows:
        print("\nВсе контакты:")
        for row in rows:
            print(f"ID: {row[0]}, Имя: {row[1]}, Телефон: {row[2]}")
    else:
        print("Контакты не найдены.")

# Меню
def menu():
    setup_db_functions()
    run = True
    while run:
        print("\nМЕНЮ PHONEBOOK:")
        print("1 - Вставка из CSV (одиночная)")
        print("2 - Добавить новый контакт (вставка или обновление)")
        print("3 - Обновить контакт")
        print("4 - Поиск контактов по шаблону")
        print("5 - Удалить контакт по ID")
        print("6 - Выход")
        print("7 - Показать все контакты")
        print("8 - Удалить все контакты")
        print("9 - Вставка нескольких контактов")
        print("10 - Запрос с пагинацией")
        print("11 - Удалить по имени или телефону")

        choice = input("Введите ваш выбор (1-11): ")

        if choice == '1':
            insert_from_csv('ph.csv')
        elif choice == '2':
            insert_or_update_contact()
        elif choice == '3':
            update_contact()
        elif choice == '4':
            search_by_pattern()
        elif choice == '5':
            delete_contact()
        elif choice == '6':
            run = False
        elif choice == '7':
            show_all_contacts()
        elif choice == '8':
            delete_all_contacts()
        elif choice == '9':
            insert_multiple_manually()
        elif choice == '10':
            query_paginated()
        elif choice == '11':
            delete_by_name_or_phone()
        else:
            print("Некорректный выбор. Попробуйте снова.")

# Запуск меню
if __name__ == "__main__":
    try:
        menu()
    except Error as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        cur.close()
        conn.close()