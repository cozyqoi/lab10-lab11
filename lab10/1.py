import psycopg2
import csv

conn = psycopg2.connect(
    database="phonebook",
    user="postgres",
    password="S4j0A2b7",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

def insert_from_csv(file_path):
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (row[0], row[1]))
    conn.commit()
    print("CSV data inserted successfully.")


def insert_from_input():
    name = input("Enter name: ")
    phone = input("Enter phone number: ")
    cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (name, phone))
    conn.commit()
    print("New contact added.")


def update_contact():
    contact_id = input("Enter ID to update: ")
    new_name = input("Enter new name: ")
    new_phone = input("Enter new phone: ")
    cur.execute("UPDATE contacts SET name = %s, phone = %s WHERE id = %s", (new_name, new_phone, contact_id))
    conn.commit()
    print("Contact updated.")


def query_with_filter():
    keyword = input("Search by name or phone: ")
    cur.execute("SELECT * FROM contacts WHERE name ILIKE %s OR phone ILIKE %s", (f'%{keyword}%', f'%{keyword}%'))
    rows = cur.fetchall()
    for row in rows:
        print(row)
    
def delete_contact():
    contact_id = input("Enter ID to delete: ")
    cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
    conn.commit()
    print("Contact deleted.")
    
def delete_all_contacts():
    cur.execute("TRUNCATE TABLE contacts RESTART IDENTITY CASCADE;")
    conn.commit()
    print("All contacts deleted.")

def show_all_contacts():
    cur.execute("SELECT * FROM contacts")
    rows = cur.fetchall()
    if rows:
        print("\nAll contacts:")
        for row in rows:
            print(f"ID: {row[0]}, Name: {row[1]}, Phone: {row[2]}")
    else:
        print("No contacts found.")


def menu():
    run = True
    while run:
        print("\nPHONEBOOK MENU:")
        print("1 - Insert from CSV")
        print("2 - Add new contact")
        print("3 - Update contact")
        print("4 - Search contacts")
        print("5 - Delete contact")
        print("6 - Exit")
        print("7 - Show all contacts")
        print("8 - Delete all contacts")

        choice = input("Enter your choice (1 or 8): ")

        if choice == '1':
            insert_from_csv('ph.csv')  # Путь к CSV-файлу, поправь если нужно
        elif choice == '2':
            insert_from_input()
        elif choice == '3':
            update_contact()
        elif choice == '4':
            query_with_filter()
        elif choice == '5':
            delete_contact()
        elif choice == '6':
            run = False
        elif choice == '7':
            show_all_contacts()
        elif choice == '8':
            delete_all_contacts()
        else:
            print("Invalid choice. Try again.")

menu()
cur.close()
conn.close()
