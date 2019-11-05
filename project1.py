import sqlite3
import sys
from getpass import getpass
from os import path
import datetime
from datetime import date
import re
import copy

connection = None
cursor = None


def main():
    # Passing the file name to the application as a command line argument
    # Check input arguments validation
    db = sys.argv[1]
    if len(sys.argv) != 2:
        print("Number of arguments should be two.")
        return
    elif not path.exists(db):
        print('No such a file.')
        return
    else:
        connect(db)
    LoginScreen()
    connection.commit()
    connection.close()


# This is a connection between the database and the python program
def connect(db):
    global connection, cursor
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    cursor.execute(' PRAGMA foreign_keys=ON; ')
    connection.commit()
    return


# Function for the login screen
def LoginScreen():
    while True:
        print("Please choose a number: 1.login  2.exit")
        user_input = input("Your option is: ")
        if user_input == '1':
            login()
        elif user_input == '2':
            quit()
        elif not user_input.isdigit():
            print("Invalid input.")
        else:
            print("No such a number.")


# This is a login option
# check if the username and password are valid to login
def login():
    global cursor
    while True:
        userid = input('Please enter your user id: ')
        cursor.execute("SELECT * FROM users WHERE uid=? COLLATE NOCASE", (userid,))
        user_id = cursor.fetchall()
        if user_id:
            password = getpass("Please enter your password: ")
            cursor.execute("SELECT uid,pwd FROM users WHERE uid=? COLLATE NOCASE AND pwd=?", (userid, password))
            exist = cursor.fetchall()
            if exist:
                print("Choose an operation.")
                cursor.execute("SELECT * FROM users WHERE utype='a'")
                type_is_agent = cursor.fetchall()
                if user_id[0] in type_is_agent:
                    menu_registry_agents(userid)
                menu_traffic_officers(userid)
            else:
                print("Invalid userid and password.")
        else:
            print("userid does not exist.")


# Options for traffic officers
def menu_traffic_officers(user_id):
    while True:
        print('---------------------------------')
        print('1. Issue a ticket')
        print('2. Find a car owner')
        print('3. logout')
        print('4. exit')
        print('---------------------------------')
        choose = input('Enter your choice(traffic officers): ')
        if choose == '1':
            Issue_ticket(user_id)
        elif choose == '2':
            find_car_owner(user_id)
        elif choose == '3':
            print('Logout successfully.')
            LoginScreen()
        elif choose == '4':
            quit()
        else:
            print('Invalid input.')


# Issue tickets operation for traffic officers
def Issue_ticket(user_id):
    global cursor, connection
    print('You are issuing tickets, please provide a registration number.')
    # Find the corresponding registration number
    registration_number = input('The registration number is: ')
    cursor.execute('''SELECT registrations.fname, registrations.lname, vehicles.make, vehicles.model, vehicles.year, vehicles.color 
                      FROM registrations, vehicles
                      WHERE registrations.vin = vehicles.vin AND registrations.regno=?''', (registration_number,))
    answer_for_find = cursor.fetchall()

    if answer_for_find:
        answer_for_find = list(answer_for_find)
        column_names = [i[0] for i in cursor.description]
        for i in answer_for_find:
            i = list(i)
            dic = dict(zip(column_names, i))
            print(dic)
        print('You can issue tickets now. Please provide the following information.')

        # Violation date
        violation_date = input(
            "The violation date is(set the value to today's date if enter nothing, format is YYYY-MM-DD): ")
        if violation_date == '' or violation_date.isspace():
            violation_date = datetime.date.today()
        else:
            valid = True
            # check valid date format
            try:
                datetime.datetime.strptime(violation_date, '%Y-%m-%d')
            except ValueError:
                valid = False
                pass
            while not valid:
                valid = False
                print('Invalid input, please try again.')
                violation_date = input(
                    "The violation date is(set the value to today's date if enter nothing, format is YYYY-MM-DD): ")
                if violation_date == '' or violation_date.isspace():
                    violation_date = datetime.date.today()
                    valid = True
                else:
                    try:
                        datetime.datetime.strptime(violation_date, '%Y-%m-%d')
                        today_date = datetime.date.today()
                        violation_date = datetime.datetime.strptime(violation_date, "%Y-%m-%d").date()
                        if violation_date <= today_date:
                            valid = True
                    except ValueError:
                        pass

        # Violation text
        violation_text = input("The violation text is: ")

        # Fine amount
        fine_amount = input("The fine amount is: ")
        while not fine_amount.isdigit():
            print('Value must be an integer, please try again.')
            fine_amount = input('The fine amount is: ')

        # Assign a unique ticket number automatically
        cursor.execute("SELECT ifnull(max(tno),0) FROM tickets")
        ticket_number = int(cursor.fetchone()[0]) + 1

        # Assigning values into tickets table
        input_values = (ticket_number, violation_date, violation_text, fine_amount, registration_number)
        cursor.execute('''INSERT INTO tickets(tno, vdate, violation, fine, regno) VALUES(?,?,?,?,?)''', input_values)
        connection.commit()
        print('Issue successfully.')
        continue_or_back = input('Continuing to issue or back to the menu? (Enter 1 for issue, 2 for back) ')
        while continue_or_back != '1' and continue_or_back != '2':
            print('Invalid input, please try again.')
            continue_or_back = input('Continuing to issue or back to the menu? (Enter 1 for issue, 2 for back) ')

        if continue_or_back == '1':
            return Issue_ticket(user_id)
        elif continue_or_back == '2':
            return menu_traffic_officers(user_id)

    # Check input for registration number
    elif not registration_number.isdigit():
        print('Please enter a number, try again.\n')
        return Issue_ticket(user_id)
    else:
        print('The registration number you entered does not exist, please try again.\n')
        return Issue_ticket(user_id)

# When there are less than 4 matches or when a car is selected from a list shown earlier,
# for each match, the make, model, year, color, and the plate of the matching car will be shown as well as the latest
# registration date, the expiry date, and the name of the person listed in the latest registration record.
def find_car_owner(user_id):
    global cursor, connection
    make = input("Please provide the make: ")
    model = input("Please provide the model: ")
    year = input("Please provide the year: ")
    color = input("Please provide the color: ")
    plate = input("Please provide the plate: ")

    # output matched results
    cursor.execute('''select make, model, year, color, plate, regdate, expiry
                              from vehicles
                              left outer join registrations r on vehicles.vin = r.vin
                              where plate is null AND (make=? COLLATE NOCASE OR model=? COLLATE NOCASE OR year=? COLLATE NOCASE OR color=? COLLATE NOCASE OR plate=? COLLATE NOCASE)
                              union
                              select make, model, year, color, plate, regdate, expiry
                              from vehicles
                              left outer join (select * from registrations group by registrations.vin order by max(regdate) DESC) AS  r on vehicles.vin = r.vin
                              where plate is not null  AND (make=? COLLATE NOCASE OR model=? COLLATE NOCASE OR year=? COLLATE NOCASE OR color=? COLLATE NOCASE OR plate=? COLLATE NOCASE)''',
                   (make, model, year, color, plate, make, model, year, color, plate,))
    result = cursor.fetchall()

    number_of_results = len(result)

    # match >= 4
    if number_of_results >= 4:
        # print each rows with numbers 1,2,3...
        count = 0
        for i in result:
            i = str(i)
            print(str(count) + ' ' + i)
            count += 1

        choice = input('Please select one (enter a number): ')
        choice = int(choice)
        find = result[choice]
        find = list(find)

        make = find[0]
        model = find[1]
        year = find[2]
        color = find[3]
        plate = find[4]

        # find a record match with user's choice
        cursor.execute('''select fname, lname
                          from vehicles
                          left outer join registrations r on vehicles.vin = r.vin
                          where plate is null AND (make=? COLLATE NOCASE AND model=? COLLATE NOCASE AND year=? COLLATE NOCASE AND color=? COLLATE NOCASE AND plate=? COLLATE NOCASE)
                          union
                          select fname, lname
                          from vehicles
                          left outer join (select * from registrations group by registrations.vin order by max(regdate) DESC) AS  r on vehicles.vin = r.vin
                          where plate is not null  AND (make=? COLLATE NOCASE AND model=? COLLATE NOCASE AND year=? COLLATE NOCASE AND color=? COLLATE NOCASE AND plate=? COLLATE NOCASE)''',
                       (make, model, year, color, plate, make, model, year, color, plate))
        name = cursor.fetchone()

        if name is None:
            print("The car has no owner.")
        else:
            # print the make, model, year, color, the plate, the latest registration date, the expiry date, the name of the person listed in the latest registration record.
            cursor.execute('''select make, model, year, color, plate, regdate, expiry, fname, lname
                              from vehicles
                              left outer join registrations r on vehicles.vin = r.vin
                              where plate is null AND (make=? COLLATE NOCASE AND model=? COLLATE NOCASE AND year=? COLLATE NOCASE AND color=? COLLATE NOCASE AND plate=? COLLATE NOCASE)
                              union
                              select make, model, year, color, plate, regdate, expiry, fname, lname
                              from vehicles
                              left outer join (select * from registrations group by registrations.vin order by max(regdate) DESC) AS  r on vehicles.vin = r.vin
                              where plate is not null  AND (make=? COLLATE NOCASE AND model=? COLLATE NOCASE AND year=? COLLATE NOCASE AND color=? COLLATE NOCASE AND plate=? COLLATE NOCASE)''',
                           (make, model, year, color, plate, make, model, year, color, plate,))
            owner = cursor.fetchone()

            owner = list(owner)
            column_names = [i[0] for i in cursor.description]
            dictionary = dict(zip(column_names, owner))
            print(dictionary)

        continue_or_back = input('Continuing to find or back to the menu? (Enter 1 for find, 2 for back) ')
        while continue_or_back != '1' and continue_or_back != '2':
            print('Invalid input, please try again.')
            continue_or_back = input('Continuing to find or back to the menu? (Enter 1 for find, 2 for back) ')
        if continue_or_back == '1':
            return find_car_owner(user_id)
        elif continue_or_back == '2':
            return menu_traffic_officers(user_id)
    # < 4, print all
    else:
        cursor.execute('''select make, model, year, color, plate, regdate, expiry, fname, lname
                          from vehicles
                          left outer join registrations r on vehicles.vin = r.vin
                          where plate is null AND (make=? COLLATE NOCASE OR model=? COLLATE NOCASE OR year=? COLLATE NOCASE OR color=? COLLATE NOCASE OR plate=? COLLATE NOCASE)
                          union
                          select make, model, year, color, plate, regdate, expiry, fname, lname
                          from vehicles
                          left outer join (select * from registrations group by registrations.vin order by max(regdate) DESC) AS  r on vehicles.vin = r.vin
                          where plate is not null  AND (make=? COLLATE NOCASE OR model=? COLLATE NOCASE OR year=? COLLATE NOCASE OR color=? COLLATE NOCASE OR plate=? COLLATE NOCASE)''',
                       (make, model, year, color, plate, make, model, year, color, plate,))
        result = cursor.fetchall()
        for i in result:
            print(i)

        continue_or_back = input('Continuing to find or back to the menu? (Enter 1 for find, 2 for back) ')
        while continue_or_back != '1' and continue_or_back != '2':
            print('Invalid input, please try again.')
            continue_or_back = input('Continuing to find or back to the menu? (Enter 1 for find, 2 for back) ')
        if continue_or_back == '1':
            return find_car_owner(user_id)
        elif continue_or_back == '2':
            return menu_traffic_officers(user_id)


def menu_registry_agents(user_id):
    while True:
        print('---------------------------------')
        print('1. Register a birth')
        print('2. Register a marriage')
        print('3. Renew a vehicle registration')
        print('4. Process a bill of sale')
        print('5. Process a payment')
        print('6. Get a driver abstract')
        print('7. logout')
        print('8. exit')
        print('---------------------------------')
        choose = input('Enter your choice(registry agents): ')
        if choose == '1':
            register_birth(user_id)
        elif choose == '2':
            register_marriage(user_id)
        elif choose == '3':
            renew_vehicle_registration(user_id)
        elif choose == '4':
            process_bill_sale(user_id)
        elif choose == '5':
            process_payment(user_id)
        elif choose == '6':
            get_driver_abstract(user_id)
        elif choose == '7':
            print('Logout successfully')
            LoginScreen()
        elif choose == '8':
            quit()
        else:
            print('Invalid input.')


def register_birth(user_id):
    global cursor, connection
    # providing the first name, the last name
    first_name = input("Please enter the first name: ")
    while first_name == '' or first_name.isspace():
        print('First name cannot be empty.')
        first_name = input("Please enter the first name: ")

    last_name = input("Please enter the last name: ")
    while last_name == '' or last_name.isspace():
        print('Last name cannot be empty.')
        last_name = input("Please enter the first name: ")

    cursor.execute('''select fname, lname from persons where fname=? COLLATE NOCASE and lname=? COLLATE NOCASE''', (first_name, last_name))
    name_exist = cursor.fetchall()
    if name_exist:
        print("The newborn name has already exist in persons database, please try again.")
        return register_birth(user_id)

    # gender
    gender = input("Please enter the gender(M or F): ").upper()
    if gender == '' or gender.isspace():
        gender = ''
    else:
        while gender != 'M' and gender != 'F':
            print("Invalid input, please try again.")
            gender = input("Please enter the gender(M or F): ").upper()

    # the birth date
    birth_date = input("Please provide the birth date(YYYY-MM-DD): ")
    if birth_date == '' or birth_date.isspace():
        birth_date = ''
    else:
        valid = True
        # check valid date format
        try:
            datetime.datetime.strptime(birth_date, '%Y-%m-%d')
        except ValueError:
            valid = False
            pass
        while not valid:
            valid = False
            print('Invalid input, please try again.')
            birth_date = input("Please provide the birth date(YYYY-MM-DD): ")
            if birth_date == '' or birth_date.isspace():
                birth_date = ''
                valid = True
            else:
                try:
                    datetime.datetime.strptime(birth_date, '%Y-%m-%d')
                    today_date = datetime.date.today()
                    birth_date = datetime.datetime.strptime(birth_date, "%Y-%m-%d").date()
                    if birth_date <= today_date:
                        valid = True
                except ValueError:
                    pass

    # the birth place
    birth_place = input('Please provide a birth place: ')

    # the first and last names of father.
    f_fname = input("Please provide father's first name: ")
    while f_fname == '' or f_fname.isspace():
        print("Father's first name cannot be empty.")
        f_fname = input("Please provide father's first name: ")
    f_lname = input("Please provide father's last name: ")
    while f_lname == '' or f_lname.isspace():
        print("Father's last name cannot be empty.")
        f_lname = input("Please provide father's last name: ")

    # check whether farther is in the system
    cursor.execute('''SELECT fname,lname FROM persons WHERE UPPER(fname) = UPPER(?) AND UPPER(lname) = UPPER(?) ''',
                   (f_fname, f_lname,))
    father_exist = cursor.fetchall() #[('Mickey', 'Mouse')]
    if not father_exist:
        print("Father's personal information did not record, please provide the following information.")
        get_person_info(f_fname, f_lname)
    else:
        father_fname = [i[0] for i in father_exist]
        father_lname = [i[1] for i in father_exist]
        f_fname = father_fname[0]
        f_lname = father_lname[0]

    # the first and last names of mother.
    m_fname = input("Please provide mother's first name: ")
    while m_fname == '' or m_fname.isspace():
        print("Mother's first name cannot be empty.")
        m_fname = input("Please provide mother's first name: ")
    m_lname = input("Please provide mother's last name: ")
    while m_lname == '' or m_lname.isspace():
        print("Mother's last name cannot be empty.")
        m_lname = input("Please provide mother's last name: ")

    # check whether mother is in the system
    cursor.execute('''SELECT fname,lname FROM persons WHERE UPPER(fname) = UPPER(?) AND UPPER(lname) = UPPER(?) ''',
                   (m_fname, m_lname,))
    mother_exist = cursor.fetchall()  # [('Mickey', 'Mouse')]

    if not mother_exist:
        print("Mother's personal information did not record, please provide the following information.")
        get_person_info(m_fname, m_lname)
    else:
        mother_fname = [i[0] for i in mother_exist]
        mother_lname = [i[1] for i in mother_exist]
        m_fname = mother_fname[0]
        m_lname = mother_lname[0]

    # The registration date is set to today's date
    registration_date = datetime.date.today()

    # The registration place = user's city
    cursor.execute('''SELECT city FROM users WHERE uid=? COLLATE NOCASE''', (str(user_id),))
    user_city = cursor.fetchall()
    user_city = [i[0] for i in user_city]
    user_city = user_city[0]
    registration_place = user_city

    # automatically assign a unique registration number to the birth record.
    cursor.execute("SELECT ifnull(max(regno),0) FROM births")
    registration_number = int(cursor.fetchone()[0]) + 1

    # The address and the phone of the newborn are set to those of the mother.
    cursor.execute('''SELECT address FROM persons WHERE fname=? AND lname=?''', (m_fname, m_lname,))
    address = cursor.fetchall()
    address = [i[0] for i in address]
    address = address[0]

    cursor.execute('''SELECT phone FROM persons WHERE fname=? AND lname=?''', (m_fname, m_lname,))
    phone = cursor.fetchall()
    phone = [i[0] for i in phone]
    phone = phone[0]

    # insert into person table
    person_values = (first_name, last_name, birth_date, birth_place, address, phone)
    cursor.execute('''INSERT INTO persons(fname, lname, bdate, bplace, address, phone) VALUES(?,?,?,?,?,?)''',
                   person_values)
    connection.commit()

    # insert into births table
    birth_values = (registration_number, first_name, last_name, registration_date, registration_place, gender, f_fname, f_lname, m_fname, m_lname)
    cursor.execute('''INSERT INTO births(regno, fname, lname, regdate, regplace, gender, f_fname, f_lname, m_fname, m_lname) 
                      VALUES(?,?,?,?,?,?,?,?,?,?)''', birth_values)
    connection.commit()

    print("Register successfully.")

    continue_or_back = input('Continuing to register or back to the menu? (Enter 1 for register, 2 for back) ')
    while continue_or_back != '1' and continue_or_back != '2':
        print('Invalid input, please try again.')
        continue_or_back = input('Continuing to register or back to the menu? (Enter 1 for register, 2 for back) ')

    if continue_or_back == '1':
        return register_birth(user_id)
    elif continue_or_back == '2':
        return menu_registry_agents(user_id)


# A function for Q1, get parents information
def get_person_info(fname, lname):
    global cursor, connection
    # the birth date
    birth_date = input("Please provide the birth date(YYYY-MM-DD): ")
    if birth_date == '' or birth_date.isspace():
        birth_date = ''
    else:
        valid = True
        # check valid date format
        try:
            datetime.datetime.strptime(birth_date, '%Y-%m-%d')
        except ValueError:
            valid = False
            pass
        while not valid:
            valid = False
            print('Invalid input, please try again.')
            birth_date = input("Please provide the birth date(YYYY-MM-DD): ")
            if birth_date == '' or birth_date.isspace():
                birth_date = ''
                valid = True
            else:
                try:
                    datetime.datetime.strptime(birth_date, '%Y-%m-%d')
                    today_date = datetime.date.today()
                    birth_date = datetime.datetime.strptime(birth_date, "%Y-%m-%d").date()
                    if birth_date <= today_date:
                        valid = True
                except ValueError:
                    pass

    bplace = input("Please provide the birth place: ")
    address = input("Please provide an address: ")

    # phone number and error checking
    valid = True
    while valid:
        phone = input("Please provide a phone number(xxx-xxx-xxxx): ")
        if phone == '' or phone.isspace():
            phone = ''
            valid = False
        else:
            check_valid = re.compile('^[0-9]{3}-[0-9]{3}-[0-9]{4}$')
            if (not check_valid.match(phone)):
                print("Invalid input, please try again.")
                valid = True
            else:
                valid = False
  

    # insert into person table
    input_values = (fname, lname, birth_date, bplace, address, phone)
    cursor.execute('''INSERT INTO persons(fname, lname, bdate, bplace, address, phone) VALUES(?,?,?,?,?,?)''',
                   input_values)
    connection.commit()


def register_marriage(user_id):
    global cursor, connection

    # the first and last names of the first partner.
    p1_fname = input("Please provide the first partner's first name: ")
    while p1_fname == '' or p1_fname.isspace():
        print("Partner's first name cannot be empty.")
        p1_fname = input("Please provide the first partner's first name: ")
    p1_lname = input("Please provide the first partner's last name: ")
    while p1_lname == '' or p1_lname.isspace():
        print("Partner's last name cannot be empty.")
        p1_lname = input("Please provide the first partner's last name: ")

    # check whether first partner is in the system
    cursor.execute('''SELECT fname,lname FROM persons WHERE UPPER(fname) = UPPER(?) AND UPPER(lname) = UPPER(?) ''',
                   (p1_fname, p1_lname,))
    p1_exist = cursor.fetchall()  # [('Mickey', 'Mouse')]
    if not p1_exist:
        print("The first partner's personal information did not record, please provide the following information.")
        get_person_info(p1_fname, p1_lname)
    else:
        p1_fname = [i[0] for i in p1_exist]
        p1_lname = [i[1] for i in p1_exist]
        p1_fname = p1_fname[0]
        p1_lname = p1_lname[0]

    # the first and last names of the second partner.
    p2_fname = input("Please provide the second partner's first name: ")
    while p2_fname == '' or p2_fname.isspace():
        print("Partner's first name cannot be empty.")
        p2_fname = input("Please provide the second partner's first name: ")
    p2_lname = input("Please provide the second partner's last name: ")
    while p2_lname == '' or p2_lname.isspace():
        print("Partner's last name cannot be empty.")
        p2_lname = input("Please provide the first partner's last name: ")

    # check whether second partner is in the system
    cursor.execute('''SELECT fname,lname FROM persons WHERE UPPER(fname) = UPPER(?) AND UPPER(lname) = UPPER(?) ''',
                   (p2_fname, p2_lname,))
    p2_exist = cursor.fetchall()  # [('Mickey', 'Mouse')]
    if not p2_exist:
        print("The second partner's personal information did not record, please provide the following information.")
        get_person_info(p2_fname, p2_lname)
    else:
        p2_fname = [i[0] for i in p2_exist]
        p2_lname = [i[1] for i in p2_exist]
        p2_fname = p2_fname[0]
        p2_lname = p2_lname[0]

    # assign the registration date = today's date
    registration_date = datetime.date.today()

    # The registration place = user's city
    cursor.execute('''SELECT city FROM users WHERE uid=? COLLATE NOCASE''', (str(user_id),))
    user_city = cursor.fetchall()
    user_city = [i[0] for i in user_city]
    user_city = user_city[0]
    registration_place = user_city

    # automatically assign a unique registration number to the marriages record.
    cursor.execute("SELECT ifnull(max(regno),0) FROM marriages")
    registration_number = int(cursor.fetchone()[0]) + 1

    # insert into marriages table
    marriage_values = (registration_number, registration_date, registration_place, p1_fname, p1_lname, p2_fname, p2_lname)
    cursor.execute('''INSERT INTO marriages(regno, regdate, regplace, p1_fname, p1_lname, p2_fname, p2_lname) 
                      VALUES(?,?,?,?,?,?,?)''', marriage_values)
    connection.commit()

    print("Register successfully.")

    continue_or_back = input('Continuing to register or back to the menu? (Enter 1 for register, 2 for back) ')
    while continue_or_back != '1' and continue_or_back != '2':
        print('Invalid input, please try again.')
        continue_or_back = input('Continuing to register or back to the menu? (Enter 1 for register, 2 for back) ')

    if continue_or_back == '1':
        return register_marriage(user_id)
    elif continue_or_back == '2':
        return menu_registry_agents(user_id)


def renew_vehicle_registration(user_id):
    global cursor, connection
    registration_number = input('Please enter an registration number to renew the registration: ')
    cursor.execute('''SELECT * FROM registrations WHERE regno=?''', (registration_number,))
    answer_for_find = cursor.fetchall()
    if answer_for_find:
        # if the current registration has expired
        # set the new expiry date to one year from today's date (2020.10.29)

        # find the expiry date
        cursor.execute('''SELECT expiry FROM registrations WHERE regno=?''', (registration_number,))
        expiry_date = cursor.fetchall()  # [('1965-05-25',),]

        # convert the date
        expiry_date = [i[0] for i in expiry_date]  # ['1965-05-25']
        expiry_date = expiry_date[0]  # '1965-05-25'
        expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()

        today_date = datetime.date.today()

        if expiry_date <= today_date:
            expiry_date = addYears(today_date, 1)
            cursor.execute('''UPDATE registrations SET expiry=? WHERE regno=?''', (expiry_date, registration_number))
            connection.commit()
        else:
            expiry_date = addYears(expiry_date, 1)
            print(expiry_date)
            cursor.execute('''UPDATE registrations SET expiry=? WHERE regno=?''', (expiry_date, registration_number))
            connection.commit()
        print('Renew successfully.')

        continue_or_back = input('Continuing to renew or back to the menu? (Enter 1 for renew, 2 for back) ')
        while continue_or_back != '1' and continue_or_back != '2':
            print('Invalid input, please try again.')
            continue_or_back = input('Continuing to renew or back to the menu? (Enter 1 for renew, 2 for back) ')

        if continue_or_back == '1':
            return renew_vehicle_registration(user_id)
        elif continue_or_back == '2':
            return menu_registry_agents(user_id)

    elif not registration_number.isdigit():
        print('Please enter a number, try again.\n')
        return renew_vehicle_registration(user_id)
    else:
        print('The registration number you entered does not exist, please try again.\n')
        return renew_vehicle_registration(user_id)


def addYears(d, years):
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))


def process_bill_sale(user_id):
    global cursor, connection

    # vin
    valid = True
    while valid:
        vin_of_car = input("Please provide the vin of a car: ")
        cursor.execute('''SELECT vin FROM registrations WHERE vin=? COLLATE NOCASE''', (vin_of_car,))
        vin = cursor.fetchall()
        if not vin:
            print("vin does not exist, please try again.")
        else:
            valid = False

    # name of current owner
    current_owner_first = input("Please provide the first name of the current owner: ")
    current_owner_last = input("Please provide the last name of the current owner: ")

    cursor.execute('''SELECT fname, lname FROM registrations WHERE vin=? COLLATE NOCASE ORDER BY regdate DESC ''', (vin_of_car,))
    real_current_owner = cursor.fetchall()
    real_current_owner_first = [i[0] for i in real_current_owner]
    real_current_owner_last = [i[1] for i in real_current_owner]
    real_current_owner_first = real_current_owner_first[0]
    real_current_owner_last = real_current_owner_last[0]

    while current_owner_first.lower() != real_current_owner_first.lower() or current_owner_last.lower() != real_current_owner_last.lower():
        print("The name of the current owner does not match the name of the most recent owner of the car in the "
              "system.")
        current_owner_first = input("Please provide the first name of the current owner: ")
        current_owner_last = input("Please provide the last name of the current owner: ")

    # name of the new owner
    exist = True
    while exist:
        new_owner_first = input("Please provide the first name of the new owner: ")
        new_owner_last = input("Please provide the last name of the new owner: ")
        cursor.execute('''SELECT fname, lname FROM persons WHERE fname=? COLLATE NOCASE AND lname=? COLLATE NOCASE''',
                       (new_owner_first, new_owner_last))
        real_new_owner = cursor.fetchall()
        if real_new_owner:
            exist = False
        else:
            print("The name of the new owner does not exist in the database.")

    # plate number
    plate_number = input("Please provide a plate number for the new registration: ")

    # the expiry date of the current registration is set to today's date
    today_date = datetime.date.today()
    cursor.execute('''UPDATE registrations SET expiry=? WHERE vin=? COLLATE NOCASE''', (today_date, vin_of_car))
    connection.commit()

    # The vin will be copied from the current registration to the new one.
    new_owner_regdate = today_date
    new_owner_expiry = addYears(today_date, 1)
    cursor.execute("SELECT ifnull(max(regno),0) FROM registrations")
    new_owner_regno = int(cursor.fetchone()[0]) + 1

    # new owner win
    cursor.execute('''SELECT vin from registrations WHERE vin=? COLLATE NOCASE''', (vin_of_car,))
    new_owner_vin = cursor.fetchall()
    new_owner_vin = [i[0] for i in new_owner_vin]
    new_owner_vin = new_owner_vin[0]

    # new owner name
    cursor.execute('''SELECT fname,lname FROM persons WHERE fname=? COLLATE NOCASE AND lname=? COLLATE NOCASE''', (new_owner_first, new_owner_last))
    new_owner_name = cursor.fetchall()
    new_owner_first = [i[0] for i in new_owner_name]
    new_owner_last = [i[1] for i in new_owner_name]
    new_owner_first = new_owner_first[0]
    new_owner_last = new_owner_last[0]

    # insert new owner values
    new_registrations = (new_owner_regno, new_owner_regdate, new_owner_expiry, plate_number, new_owner_vin, new_owner_first, new_owner_last)
    cursor.execute('''INSERT INTO registrations(regno, regdate, expiry, plate, vin, fname, lname) 
                          VALUES(?,?,?,?,?,?,?)''', new_registrations)
    connection.commit()

    print("Process successfully.")

    continue_or_back = input('Continuing to process or back to the menu? (Enter 1 for process, 2 for back) ')
    while continue_or_back != '1' and continue_or_back != '2':
        print('Invalid input, please try again.')
        continue_or_back = input('Continuing to process or back to the menu? (Enter 1 for process, 2 for back) ')

    if continue_or_back == '1':
        return process_bill_sale(user_id)
    elif continue_or_back == '2':
        return menu_registry_agents(user_id)


def process_payment(user_id):
    global cursor, connection
    ticket_number = input('Please enter a ticket number: ')

    cursor.execute('''SELECT * FROM tickets WHERE tickets.tno=?''', (ticket_number,))
    answer_for_find = cursor.fetchall()

    cursor.execute('''SELECT fine FROM tickets WHERE tickets.tno=?''', (ticket_number,))
    fine_amount = cursor.fetchall()

    current_amount_in_payments_list = list(
        cursor.execute('''SELECT amount FROM payments WHERE payments.tno=?''', (ticket_number,)))

    # If list is empty, set to 0. If not, calculate the sum of the total current payment
    if not current_amount_in_payments_list:
        current_amount_in_payments = 0
    else:
        remove_comma = [map(str, i) for i in current_amount_in_payments_list]
        current_amount_in_payments_list = [int(''.join(i)) for i in remove_comma]  # fine_amount = [4]
        current_amount_in_payments = sum(current_amount_in_payments_list)

    # If ticket number exist in the tickets table
    if answer_for_find:
        amount = input('Please enter an amount: ')

        # error check for input
        while not amount.isdigit():
            print('Value is not an integer, please try again.')
            amount = input('Please enter an amount: ')

        # convert the fine amount in tickets table to an integer
        remove_comma = [map(str, i) for i in fine_amount]
        fine_amount = [int(''.join(i)) for i in remove_comma]  # fine_amount = [4]
        fine_amount = int(fine_amount[0])

        # decide whether payment entered exceeds
        remaining_amount = fine_amount - current_amount_in_payments
        while int(amount) + current_amount_in_payments > fine_amount:
            if remaining_amount == 0:
                print('The fine for this ticket has already been paid completely. ')
                return process_payment(user_id)
            print('The sum of payments exceed the fine amount of the ticket.')
            print('The amount you entered should be less than or equal to ' + str(remaining_amount) + '.')
            print('Please try again.')
            amount = input('Please enter an amount: ')

        payment_date = datetime.date.today()
        input_values = (ticket_number, amount, payment_date)
        cursor.execute('''INSERT INTO payments(tno, amount, pdate) VALUES(?,?,?)''', input_values)
        connection.commit()
        print('Recording payment successfully.')

        continue_or_back = input('Continuing to record or back to the menu? (Enter 1 for record, 2 for back) ')

        while continue_or_back != '1' and continue_or_back != '2':
            print('Invalid input, please try again.')
            continue_or_back = input('Continuing to record or back to the menu? (Enter 1 for record, 2 for back) ')

        if continue_or_back == '1':
            return process_payment(user_id)
        elif continue_or_back == '2':
            return menu_registry_agents(user_id)

    elif not ticket_number.isdigit():
        print('Please enter a number, try again.\n')
        return process_payment(user_id)
    else:
        print('The ticket number you entered does not exist, please try again.\n')
        return process_payment(user_id)


def get_driver_abstract(user_id):
    global cursor, connection

    # get a driver abstract
    first_name = input("Please enter the first name: ")
    last_name = input("Please enter the last name: ")
    cursor.execute('''SELECT count(tno) AS number_of_tickets, count(ddate) AS number_of_demeritnotices, ifnull(sum(points), 0) AS total_demeritpoints
                      FROM persons
                      LEFT OUTER JOIN registrations r on persons.fname = r.fname and persons.lname = r.lname
                      LEFT OUTER JOIN (SELECT *
                                       FROM tickets
                                       WHERE (JULIANDAY('now') - JULIANDAY(vdate) <= JULIANDAY('now') - JULIANDAY('now', '-2 year'))) AS t on r.regno = t.regno
                      LEFT JOIN (SELECT *
                                 FROM demeritNotices
                                  WHERE (JULIANDAY('now') - JULIANDAY(ddate) <= JULIANDAY('now') - JULIANDAY('now', '-2 year'))) AS demeritNotices USING (fname,lname)
                      WHERE persons.fname=? COLLATE NOCASE AND persons.lname=? COLLATE NOCASE
                      GROUP BY persons.fname, persons.lname''', (first_name, last_name))

    driver_abstract = cursor.fetchone()
    if driver_abstract:
        driver_abstract = list(driver_abstract)
        column_names = [i[0] for i in cursor.description]
        dictionary = dict(zip(column_names, driver_abstract))
        print(dictionary)

        see_tickets = input("Do you want to see the tickets? (1 for yes, 2 for no) ")
        while see_tickets != '1' and see_tickets != '2':
            print("Invalid input, please try again.")
            see_tickets = input("Do you want to see the tickets? (1 for yes, 2 for no) ")

        if see_tickets == '1':
            cursor.execute('''SELECT tno, vdate, violation, fine, r.regno, make, model
                              FROM persons
                              LEFT OUTER JOIN registrations r on persons.fname = r.fname and persons.lname = r.lname
                              LEFT OUTER JOIN (SELECT *
                                               FROM tickets
                                               WHERE (JULIANDAY('now') - JULIANDAY(vdate) <= JULIANDAY('now') - JULIANDAY('now', '-2 year'))
                                               ORDER BY vdate DESC ) AS t on r.regno = t.regno
                              LEFT OUTER JOIN vehicles v on r.vin = v.vin
                              WHERE (persons.fname=? COLLATE NOCASE AND persons.lname=? COLLATE NOCASE) AND tno is not null''', (first_name, last_name))
            tickets_info = cursor.fetchall()

            column_names = [i[0] for i in cursor.description]

            num_of_rows = len(tickets_info)

            if num_of_rows <= 5:
                for i in tickets_info:
                    i = list(i)
                    dic = dict(zip(column_names, i))
                    print(dic)
            else:
                copy_info = []
                while num_of_rows > 5:
                    copy_info.clear()
                    del copy_info
                    copy_info = copy.deepcopy(tickets_info)
                    count = 0
                    for information in tickets_info:
                        information = list(information)
                        dic = dict(zip(column_names, information))
                        print(dic)
                        del(copy_info[0])
                        count += 1
                        if count == 5:
                            tickets_info.clear()
                            del tickets_info
                            tickets_info = copy.deepcopy(copy_info)
                            break
                    choice = input("There are more than 5 tickets, Do you want to see more? (1 for yes, 2 for back) ")
                    while choice != '1' and choice != '2':
                        print("Invalid input. please try again.")
                        choice = input("There are more than 5 tickets, Do you want to see more? (1 for yes, 2 for back) ")
                    if choice == '2':
                        return get_driver_abstract(user_id)
                    else:
                        num_of_rows = num_of_rows - 5
                for i in tickets_info:
                    i = list(i)
                    dic = dict(zip(column_names, i))
                    print(dic)

            print('No more tickets.')
            choice = input("Back to get another driver abstract or back to the menu? (1 for get, 2 for menu) ")
            while choice != '1' and choice != '2':
                print("Invalid input, please try again.")
                choice = input("Back to get another driver abstract or back to the menu? (1 for get, 2 for menu) ")
            if choice == '1':
                return get_driver_abstract(user_id)
            else:
                return menu_registry_agents(user_id)

        elif see_tickets == '2':
            choice = input("Back to get another driver abstract or back to the menu? (1 for get, 2 for menu) ")
            while choice != '1' and choice != '2':
                print("Invalid input, please try again.")
                choice = input("Back to get another driver abstract or back to the menu? (1 for get, 2 for menu) ")
            if choice == '1':
                return get_driver_abstract(user_id)
            else:
                return menu_registry_agents(user_id)
    else:
        print("The name you provided is not in the database, please try again.")
        return get_driver_abstract(user_id)


if __name__ == "__main__":
    main()
