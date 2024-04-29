# Importing all necessary modules
import sqlite3
from tkinter import *
import tkinter.ttk as ttk
import tkinter.messagebox as mb
import tkinter.simpledialog as sd
from datetime import datetime
import re

# Connecting to Database
connector = sqlite3.connect('library.db')
cursor = connector.cursor()

# Create necessary tables if not exist
tables = {
    'Books': ['Book_Name TEXT', 'Book_ID TEXT PRIMARY KEY NOT NULL', 'Author_Name TEXT', 'Status TEXT', 'Card_ID TEXT'],
    'Users': ['User_ID TEXT PRIMARY KEY NOT NULL', 'Name TEXT', 'Email TEXT'],
    'Transactions': ['Transaction_ID INTEGER PRIMARY KEY AUTOINCREMENT', 'Book_ID TEXT', 'User_ID TEXT', 'Date TEXT'],
    'Categories': ['Category_ID INTEGER PRIMARY KEY AUTOINCREMENT', 'Category_Name TEXT'],
    'Publishers': ['Publisher_ID INTEGER PRIMARY KEY AUTOINCREMENT', 'Publisher_Name TEXT'],
    'Relationships': ['Book_ID TEXT', 'Category_ID INTEGER', 'Publisher_ID INTEGER']
}

for table, columns in tables.items():
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})")

# Functions
def issuer_card():
    Cid = sd.askstring('Issuer Card ID', 'What is the Issuer\'s Card ID?\t\t\t')

    if not Cid:
        mb.showerror('Issuer ID cannot be zero!', 'Can\'t keep Issuer ID empty, it must have a value')
    else:
        return Cid

def display_records(table_name):
    global connector, cursor
    global tree

    tree.delete(*tree.get_children())

    curr = cursor.execute(f'SELECT * FROM {table_name}')
    data = curr.fetchall()

    for records in data:
        tree.insert('', END, values=records)

def clear_fields():
    global bk_status, bk_id, bk_name, author_name, card_id

    bk_status.set('Available')
    for var in [bk_id, bk_name, author_name, card_id]:
        var.set('')
    bk_id_entry.config(state='normal')
    try:
        tree.selection_remove(tree.selection()[0])
    except:
        pass

def clear_and_display(table_name):
    clear_fields()
    display_records(table_name)

def add_record(table_name):
    global cursor, connector
    global bk_name, bk_id, author_name, bk_status, card_id

    # Check if any of the required fields are empty
    if not all([bk_name.get(), bk_id.get(), author_name.get()]):
        mb.showerror('Incomplete Information', 'Please fill in all the required fields.')
        return

    # Check if the entered Book ID already exists
    cursor.execute('SELECT * FROM Books WHERE Book_ID=?', (bk_id.get(),))
    existing_book = cursor.fetchone()
    if existing_book:
        mb.showerror('Book ID Already Exists', 'The entered Book ID already exists. Please enter a unique Book ID.')
        return

    if bk_status.get() == 'Issued':
        mb.showerror('Status Error', 'Cannot add record with status "Issued". Please use the "Change Availability" button for this.')
        return

    # If status is 'Available', set card_id to NULL
    card_id_value = None if bk_status.get() == 'Available' else issuer_card()

    # Prompt for publisher ID and name
    publisher_id = sd.askstring('Publisher ID', 'Enter the Publisher ID:')
    publisher_name = sd.askstring('Publisher Name', 'Enter the Publisher Name:')

    # Prompt for category ID and name
    category_id = sd.askstring('Category ID', 'Enter the Category ID:')
    category_name = sd.askstring('Category Name', 'Enter the Category Name:')

    
    surety = mb.askyesno('Are you sure?', 'Are you sure this is the data you want to enter?\nPlease note that Book ID cannot be changed in the future')

    if surety:
        try:
            cursor.execute(f'INSERT INTO {table_name} (Book_Name, Book_ID, Author_Name, Status, Card_ID) VALUES (?, ?, ?, ?, ?)',
                           (bk_name.get(), bk_id.get(), author_name.get(), bk_status.get(), card_id_value))
            connector.commit()

            # Insert publisher and category information into respective tables
            cursor.execute('INSERT INTO Publishers (Publisher_ID, Publisher_Name) VALUES (?, ?)', (publisher_id, publisher_name))
            cursor.execute('INSERT INTO Categories (Category_ID, Category_Name) VALUES (?, ?)', (category_id, category_name))

            # Insert relationship between book, publisher, and category into Relationships table
            cursor.execute('INSERT INTO Relationships (Book_ID, Category_ID, Publisher_ID) VALUES (?, ?, ?)', (bk_id.get(), category_id, publisher_id))

            clear_and_display(table_name)

            mb.showinfo('Record added', 'The new record was successfully added to your database')
        except sqlite3.IntegrityError:
            mb.showerror('Book ID already in use!',
                         'The Book ID you are trying to enter is already in the database, please alter that book\'s record or check any discrepancies on your side')

def search_by_author():
    author = sd.askstring('Search by Author', 'Enter the author\'s name:')
    if not author:
        return
    display_records('Books')
    tree.tag_configure('found', background='yellow')
    for item in tree.get_children():
        if author.lower() in tree.item(item)['values'][2].lower():
            tree.item(item, tags=('found',))
        else:
            tree.item(item, tags=())

def search_by_book_name():
    global tree

    book_name = sd.askstring('Search by Book Name', 'Enter the book\'s name : If you want proper enter full book name ')
    if not book_name:
        return

    display_records('Books')

    # Count available books
    available_count = 0
    for item in tree.get_children():
        if book_name.lower() in tree.item(item)['values'][0].lower():
            if tree.item(item)['values'][3] == 'Available':
                available_count += 1
            tree.item(item, tags=('found',))
        else:
            tree.item(item, tags=())

    # Ask if user wants to know the available count
    if mb.askyesno('Available Book Count', f'Do you want to know the available count of "{book_name}" in the inventory?\nAvailable Count: {available_count}'):
        mb.showinfo('Available Book Count', f'The available count of "{book_name}" in the inventory is: {available_count}')

def remove_record(table_name):
    if not tree.selection():
        mb.showerror('Error!', 'Please select an item from the database')
        return

    current_item = tree.focus()
    values = tree.item(current_item)
    selection = values["values"]

    cursor.execute(f'DELETE FROM {table_name} WHERE Book_ID=?', (selection[1], ))
    connector.commit()

    tree.delete(current_item)

    mb.showinfo('Done', 'The record you wanted deleted was successfully deleted.')

    clear_and_display(table_name)

def delete_inventory(table_name):
    if mb.askyesno('Are you sure?', 'Are you sure you want to delete the entire inventory?\n\nThis command cannot be reversed'):
        tree.delete(*tree.get_children())

        cursor.execute(f'DELETE FROM {table_name}')
        connector.commit()
    else:
        return


def view_record():
    global bk_name, bk_id, bk_status, author_name, card_id
    global tree

    if not tree.focus():
        mb.showerror('Select a row!', 'To view a record, you must select it in the table. Please do so before continuing.')
        return

    current_item_selected = tree.focus()
    values_in_selected_item = tree.item(current_item_selected)
    selection = values_in_selected_item['values']

    bk_name.set(selection[0])
    bk_id.set(selection[1])
    bk_status.set(selection[3])
    author_name.set(selection[2])
    try:
        card_id.set(selection[4])
    except:
        card_id.set('')


# Update the update_record function to remove the option of changing Book ID
def update_record(table_name):
    def update():
        global bk_name, author_name
        global cursor, tree

        # Retrieve the currently selected item in the treeview
        if not tree.selection():
            mb.showerror('Select a row!', 'To update a record, you must select it in the table. Please do so before continuing.')
            return

        current_item_selected = tree.focus()
        values_in_selected_item = tree.item(current_item_selected)
        selection = values_in_selected_item['values']

        # Retrieve the Book ID
        bk_id_to_update = selection[1]

        # Retrieve the updated values for Book Name and Author Name
        updated_bk_name = bk_name.get()
        updated_author_name = author_name.get()

        # Update the record only if Book Name or Author Name is changed
        if updated_bk_name != selection[0] or updated_author_name != selection[2]:
            cursor.execute(f'UPDATE {table_name} SET Book_Name=?, Author_Name=? WHERE Book_ID=?',
                           (updated_bk_name, updated_author_name, bk_id_to_update))
            connector.commit()

            # Clear and display records to reflect the update in the UI
            clear_and_display(table_name)

            # Show confirmation message
            mb.showinfo('Record Updated', 'The record has been successfully updated.')
        else:
            mb.showinfo('No Changes', 'No changes were made to the record.')

        # Close the update window
        edit.destroy()
        clear.config(state='normal')

    # Call the view_record() function to populate the entry fields with the selected record's data
    view_record()

    # Disable the clear button while updating
    clear.config(state='disabled')

    # Create the Update Record button
    edit = Button(left_frame, text='Update Record', font=btn_font, bg=btn_hlb_bg, width=20, command=update)
    edit.place(x=50, y=375)

    # Clear and display records in case user wants to make changes to availability or status
    clear_and_display('Books')


# Update the change_availability function to prompt for issuance date and issuer ID only when changing the status to "Issued"

def is_valid_email(email):
    # Regular expression pattern for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

def is_valid_date(date_text):
    try:
        datetime.strptime(date_text, '%d-%m-%Y')
        return True
    except ValueError:
        return False

def change_availability():
    global cursor, connector

    if not tree.selection():
        mb.showerror('Error!', 'Please select a book from the database')
        return

    current_item = tree.focus()
    values = tree.item(current_item)
    BK_id = values['values'][1]
    BK_status = values["values"][3]

    if BK_status == 'Available':
        issuance_date = sd.askstring('Issuance Date', 'Enter the date of issuance (DD-MM-YYYY):')
        issuer_id = sd.askstring('Issuer ID', 'Enter the Issuer ID:')
        
        # Check if the issuer ID already exists in the Users table
        cursor.execute('SELECT * FROM Users WHERE User_ID=?', (issuer_id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            # If the user doesn't exist, prompt for name and email
            user_name = sd.askstring('User Name', 'Enter the User Name:')
            user_email = sd.askstring('User Email', 'Enter the User Email ID:')
            if not user_name or not user_email:
                mb.showerror('Incomplete Information', 'User Name and User Email are required.')
                return

            # Validate the email format
            if not is_valid_email(user_email):
                mb.showerror('Invalid Email', 'Please enter a valid email address.')
                return

            # Insert the new user information into the Users table
            cursor.execute('INSERT INTO Users (User_ID, Name, Email) VALUES (?, ?, ?)', (issuer_id, user_name, user_email))
        else:
            # If the user exists, retrieve their name and email from the database
            user_name = existing_user[1]
            user_email = existing_user[2]

        # Validate the issuance date format
        if not is_valid_date(issuance_date):
            mb.showerror('Invalid Date', 'Please enter the date in DD-MM-YYYY format.')
            return

        # Update the book status and card ID in the Books table
        cursor.execute('UPDATE Books SET Status=?, Card_ID=? WHERE Book_ID=?', ('Issued', issuer_id, BK_id))

        # Insert the issuance record into the Transactions table
        cursor.execute('INSERT INTO Transactions (Book_ID, User_ID, Date) VALUES (?, ?, ?)', (BK_id, issuer_id, issuance_date))
        
        connector.commit()

        # Display the updated record
        clear_and_display('Books')

        # Show confirmation message
        mb.showinfo('Record Updated', 'The record status has been updated to "Issued".')
    else:
        mb.showinfo('Book Already Issued', 'The selected book is already issued.')


def return_book():
    global cursor, connector

    # Prompt for Issuer ID and Book ID
    issuer_id = sd.askstring('Issuer ID', 'Enter the Issuer ID:')
    if not issuer_id:
        return

    book_id = sd.askstring('Book ID', 'Enter the Book ID:')
    if not book_id:
        return

    # Check if the issuer ID and book ID exist in the database
    cursor.execute('SELECT * FROM Users WHERE User_ID=?', (issuer_id,))
    issuer_exists = cursor.fetchone()

    cursor.execute('SELECT * FROM Books WHERE Book_ID=?', (book_id,))
    book_exists = cursor.fetchone()

    if not issuer_exists:
        mb.showerror('Issuer ID Not Found', 'The specified Issuer ID does not exist.')
        return

    if not book_exists:
        mb.showerror('Book ID Not Found', 'The specified Book ID does not exist.')
        return

    # Retrieve issuing date of the book
    cursor.execute('SELECT Date FROM Transactions WHERE Book_ID=? AND User_ID=?', (book_id, issuer_id))
    issuing_date = cursor.fetchone()

    if not issuing_date:
        mb.showerror('No Record Found', 'No record found for the specified Issuer ID and Book ID.')
        return

    issuing_date = datetime.strptime(issuing_date[0], '%d-%m-%Y')
    return_date = datetime.now()
    days_difference = (return_date - issuing_date).days

    # Calculate bill
    bill = max(0, days_difference - 30) * 10  # Rs. 10 per month after issuing date

    mb.showinfo('Bill Calculation', f'The bill for returning the book is: Rs. {bill}')

    # Update book status to available
    cursor.execute('UPDATE Books SET Status=?, Card_ID=? WHERE Book_ID=?', ('Available', 'N/A', book_id))
    connector.commit()

    # Remove transaction record
    cursor.execute('DELETE FROM Transactions WHERE Book_ID=? AND User_ID=?', (book_id, issuer_id))
    connector.commit()

    clear_and_display('Books')

def check_issued_books():
    global cursor, connector

    issuer_id = sd.askstring('Issuer ID', 'Enter the Issuer ID:')
    if not issuer_id:
        return

    # Retrieve issued books for the specified issuer ID
    cursor.execute('SELECT Book_ID, Date FROM Transactions WHERE User_ID=?', (issuer_id,))
    issued_books = cursor.fetchall()

    if not issued_books:
        mb.showinfo('No Issued Books', f'No books are issued to the user with ID: {issuer_id}')
    else:
        book_list = '\n'.join([f'Book ID: {book[0]}, Issuing Date: {book[1]}' for book in issued_books])
        mb.showinfo('Issued Books', f'Books issued to user with ID {issuer_id}:\n\n{book_list}')

def display_user_details():
    global cursor

    # Retrieve all user details from the Users table
    cursor.execute('SELECT * FROM Users')
    user_details = cursor.fetchall()

    if not user_details:
        mb.showinfo('No Users', 'No user details found in the database.')
    else:
        # Prepare user details for display
        user_details_str = '\n'.join([f'User ID: {user[0]}, Name: {user[1]}, Email: {user[2]}' for user in user_details])
        mb.showinfo('User Details', f'User Details:\n\n{user_details_str}')

# Variables
lf_bg = '#758467'  # Left Frame Background Color
rtf_bg = '#819171'  # Right Top Frame Background Color
rbf_bg = '#9CAF88'  # Right Bottom Frame Background Color
btn_hlb_bg = '#CBD5C0'  # Background color for Head Labels and Buttons

lbl_font = ('Georgia', 13)  # Font for all labels
entry_font = ('Times New Roman', 12)  # Font for all Entry widgets
btn_font = ('Gill Sans MT', 13)

# Initializing the main GUI window
root = Tk()
root.title('Library Management System')
root.geometry('1010x1010')
root.resizable(True, True)

Label(root, text='LIBRARY MANAGEMENT SYSTEM', font=("Noto Sans CJK TC", 15, 'bold'), bg=btn_hlb_bg, fg='Black').pack(side=TOP, fill=X)

# StringVars
bk_status = StringVar()
bk_name = StringVar()
bk_id = StringVar()
author_name = StringVar()
card_id = StringVar()

# Frames
left_frame = Frame(root, bg=lf_bg)
left_frame.place(x=0, y=30, relwidth=0.3, relheight=0.96)

RT_frame = Frame(root, bg=rtf_bg)
RT_frame.place(relx=0.3, y=30, relheight=0.2, relwidth=0.7)

RB_frame = Frame(root)
RB_frame.place(relx=0.3, rely=0.24, relheight=0.785, relwidth=0.7)

# Left Frame
Label(left_frame, text='Book Name', bg=lf_bg, font=lbl_font).place(x=98, y=25)
Entry(left_frame, width=25, font=entry_font, text=bk_name).place(x=45, y=55)

Label(left_frame, text='Book ID', bg=lf_bg, font=lbl_font).place(x=110, y=105)
bk_id_entry = Entry(left_frame, width=25, font=entry_font, text=bk_id)
bk_id_entry.place(x=45, y=135)

Label(left_frame, text='Author Name', bg=lf_bg, font=lbl_font).place(x=90, y=185)
Entry(left_frame, width=25, font=entry_font, text=author_name).place(x=45, y=215)

Label(left_frame, text='Status of the Book', bg=lf_bg, font=lbl_font).place(x=75, y=265)
dd = OptionMenu(left_frame, bk_status, *['Available', 'Issued'])
dd.configure(font=entry_font, width=12)
dd.place(x=75, y=300)

submit = Button(left_frame, text='Add new record', font=btn_font, bg=btn_hlb_bg, width=20, command=lambda: add_record('Books'))
submit.place(x=50, y=375)

clear = Button(left_frame, text='Clear fields', font=btn_font, bg=btn_hlb_bg, width=20, command=clear_fields)
clear.place(x=50, y=435)

search_author_btn = Button(left_frame, text='Search by Author', font=btn_font, bg=btn_hlb_bg, width=20, command=search_by_author)
search_author_btn.place(x=50, y=495)

search_book_btn = Button(left_frame, text='Search by Book Name', font=btn_font, bg=btn_hlb_bg, width=20, command=search_by_book_name)
search_book_btn.place(x=50, y=555)

# Right Top Frame
view = Button(RT_frame, text='View Record', font=btn_font, bg=btn_hlb_bg, width=20, command=view_record)
view.grid(row=0, column=0, padx=20, pady=20)

update = Button(RT_frame, text='Update Record', font=btn_font, bg=btn_hlb_bg, width=20, command=lambda: update_record('Books'))
update.grid(row=0, column=1, padx=20, pady=20)

remove = Button(RT_frame, text='Remove Record', font=btn_font, bg=btn_hlb_bg, width=20, command=lambda: remove_record('Books'))
remove.grid(row=0, column=2, padx=20, pady=20)

change_status = Button(RT_frame, text='Change Availability', font=btn_font, bg=btn_hlb_bg, width=20, command=change_availability)
change_status.grid(row=0, column=3, padx=20, pady=20)

# Right Bottom Frame
RB_frame = Frame(root)
RB_frame.place(relx=0.3, rely=0.24, relheight=0.785, relwidth=0.7)

# Create Treeview with scrollbars
tree = ttk.Treeview(RB_frame, column=('Book Name', 'Book ID', 'Author Name', 'Status', 'Card ID'), show='headings', height=20)
tree.heading('Book Name', text='Book Name')
tree.heading('Book ID', text='Book ID')
tree.heading('Author Name', text='Author Name')
tree.heading('Status', text='Status')
tree.heading('Card ID', text='Card ID')

# Vertical Scrollbar
vsb = ttk.Scrollbar(RB_frame, orient="vertical", command=tree.yview)
vsb.pack(side="right", fill="y")
tree.configure(yscrollcommand=vsb.set)

# Horizontal Scrollbar
hsb = ttk.Scrollbar(RB_frame, orient="horizontal", command=tree.xview)
hsb.pack(side="bottom", fill="x")
tree.configure(xscrollcommand=hsb.set)

tree.pack(expand=True, fill="both")

# Menu Bar
menubar = Menu(root)
root.config(menu=menubar)

file_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label='File', menu=file_menu)
file_menu.add_command(label='Delete Inventory', command=lambda: delete_inventory('Books'))
file_menu.add_command(label='Exit', command=root.destroy)

book_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label='Books', menu=book_menu)
book_menu.add_command(label='View Issued Books', command=check_issued_books)

return_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label='Return Book', menu=return_menu)
return_menu.add_command(label='Return Book', command=return_book)

user_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label='Users', menu=user_menu)
user_menu.add_command(label='View User Details', command=display_user_details)

# Functions for the buttons
clear_and_display('Books')
root.mainloop()                                                                                                                                  