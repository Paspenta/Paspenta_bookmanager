from werkzeug.security import generate_password_hash

password = input("password:")
print(generate_password_hash(password))
