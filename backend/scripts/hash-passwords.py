import bcrypt

from backend import db
from backend.models import User


def main():
    users = User.query.all()
    for user in users:
        print('Fixing user %s, %s.' % (user.email_address, user.password_hash))
        user.password_salt = bcrypt.gensalt()
        user.password_hash = bcrypt.hashpw(user.password_hash.encode('utf-8'), user.password_salt)
        db.session.add(user)
        db.session.commit()


if __name__ == '__main__':
    main()