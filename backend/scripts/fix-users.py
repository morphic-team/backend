from backend import db
from backend.models import User, Session, ResultField, SurveyField, Search, Survey, *
from backend.models import *

# Number of result fields before a none user is considered special.
RESULT_FIELD_CAP = 1

# Remove all users with an email address of None.
none_users = User.query.filter_by(email_address=None).all()

# Double check that the none users have a password.
assert not any([none_user.password_hash for none_user in none_users]) 

for none_user in none_users:
    searches = Search.query.join(Search.survey).filter(Survey.user_id==none_user.id_).all()
    for search in searches:
        db.session.delete(search)
    db.session.commit()

for none_user in none_users:
    print('checking none user:', none_user.id_)
    # Double check that the none users have content.
    # if none_user.searches:
    #     print('skipping none user (searches)', none_user.id_)
    #     continue
    # if none_user.surveys:
    #     print('skipping none user (surveys)', none_user.id_)
    #     continue
    # Check for actual useful work by none user.
    print('checking none user', none_user.id_)
    # for survey in none_user.surveys:
    #     print('checking survey', survey.id_, survey.name)
    #     result_fields = ResultField.query.join(ResultField.survey_field).filter(SurveyField.survey_id==survey.id_).all()
    #     print('result field count', len(result_fields))
    #     if (len(result_fields) > RESULT_FIELD_CAP):
    #         print('skipping none user (result fields)')
    #         continue
    sessions = Session.query.filter(Session.user==none_user).all()
    if sessions:
        print('fixing none user (sessions)', none_user.id_)
        for session in sessions:
            db.session.delete(session)
    # print('fixing none user (searches)', none_user.id_)
    # searches = Search.query.join(Search.survey).filter(Survey.user_id==none_user.id_).all()
    # for search in searches:
    #     db.session.delete(search)
    # # Delete the none users.
    # print('deleting none user:', none_user.id_)
    db.session.delete(none_user)
    db.session.commit()


# Build general purpose datastructures.
from collections import defaultdict, Counter
all_users = User.query.all()
user_map = defaultdict(lambda: list())
user_counter = Counter()

for user in all_users:
    user_map[user.email_address].append(user)
    user_counter[user.email_address] += 1

for email_address, count in user_counter.items():
    if count == 1:
        continue
    users = user_map[email_address]
    for user in users:
        print(email_address, user.id_, len(user.searches), len(user.surveys))

USERS_TO_DELETE = [
    297,
    249,
    247,
    248,
    294,
    5,
    42,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    28,
    162,
    163,
    4,
    122,
    328,
    329,
    330,
    331,
    332,
    333,
    334,
    335,
    336,
    337,
    338,
    339,
    302,
    310,
    62,
    309,
    291,
    344,
    343,
]

def do():
    for user_id in USERS_TO_DELETE:
        user = User.query.filter_by(id_=user_id).first()
        if user is None:
            continue
        sessions = Session.query.filter(Session.user==user).all()
        if sessions:
            print('fixing user (sessions)', user.id_)
            for session in sessions:
                db.session.delete(session)
        print('fixing user (searches)', user.id_)
        searches = Search.query.join(Search.survey).filter(Survey.user_id==user.id_).all()
        for search in searches:
            db.session.delete(search)
            db.session.commit()
            return
        db.session.delete(user)
        db.session.commit()