import json
import boto3
import uuid
import secrets
import datetime

from passlib.hash import pbkdf2_sha256

USERS_TABLE_NAME = "FinalProjUsers"
POSTS_TABLE_NAME = "FinalProjPosts"
NO_SUCCESS = {'success': False}

db = None

"""Function to create user in dynamo

Parameters
----------
email: user email, required
passwd: user password, required

Returns
----------
dict containing success value, user id, user session token

"""


def create_user(email, passwd):
    if not email or not passwd:
        raise ValueError("Email or password not given")

    # Check if user email is already taken
    resp = db.query(
        TableName=USERS_TABLE_NAME,
        IndexName="email-index",
        ExpressionAttributeValues={
            ':v': {
                'S': email
            }
        },
        KeyConditionExpression='email = :v'
    )
    items = resp.get('items')
    if items:
        return {'success': False}

    # Hash user password using pbkdf2
    pwd_hash = pbkdf2_sha256.hash(passwd)
    user_id = str(uuid.uuid1())

    # Generate random secret, then hash it and return to client as session token
    session_secret = secrets.token_urlsafe(16)
    session_hash = pbkdf2_sha256.hash(session_secret)

    # Session tokens expire 1 week from creation date
    # Create datetime str for expiration date, and store with current secret
    token_expire_time = str(datetime.datetime.now() + datetime.timedelta(days=7))

    db.put_item(TableName=USERS_TABLE_NAME, Item={
        'uuid': {"S": user_id},
        'email': {"S": email},
        'pwd_hash': {"S": pwd_hash},
        'session_secret': {"S": session_secret},
        'expire_time': {"S": token_expire_time}
    })

    return {
        'success': True,
        'uuid': user_id,
        'token': session_hash
    }


"""Function to create user in dynamo

Parameters
----------
email: user email, required
passwd: user password, required

Returns
----------
dict containing success value, user_id, session token

"""


def login(email, passwd):
    if not email or not passwd:
        raise ValueError("Email or password not given")

    resp = db.get_item(
        TableName=USERS_TABLE_NAME,
        Key={
            'email-index': email
        }
    )
    item = resp['Item']
    # Fail if user does not exist
    if not item:
        return NO_SUCCESS

    # Fail if verification fails
    if not pbkdf2_sha256.verify(passwd, item['pwd_hash']):
        return NO_SUCCESS

    # Create new session secret, hash, expire time
    session_secret = secrets.token_urlsafe(16)
    session_hash = pbkdf2_sha256.hash(session_secret)
    token_expire_time = str(datetime.datetime.now() + datetime.timedelta(days=7))

    db.update_item(
        TableName=USERS_TABLE_NAME,
        Key=item,
        UpdateExpression="set session_secret = :s, expire_time = :t",
        ExpressionAttributeValues={
            ':s': session_secret,
            ':t': token_expire_time
        }
    )

    return {
        'success': True,
        'uuid': item['uuid'],
        'token': session_hash
    }


def verify_session(user_id, token):
    resp = db.get_item(
        TableName=USERS_TABLE_NAME,
        Key={
            'uuid': user_id
        }
    )
    item = resp['Item']
    # Fail if user does not exist
    if not item:
        return False

    return pbkdf2_sha256.verify(item['session_secret'], token)


def lambda_handler(event, context):
    global db
    db = boto3.client("dynamodb")
    action = None
    method = None
    email = None
    passwd = None
    body = None
    output = None
    invalid = {
            'statusCode': 403,
            'body': "Invalid protocol"
    }

    invalid2 = {
            'statusCode': 403,
            'body': "adfadsfasdf"
    }

    try:
        action = event['pathParameters']['action'].split('/')
        method = event['httpMethod']
        body = json.loads(event["body"])
        email = body['email']
        passwd = body["password"]
    except KeyError:
        return invalid



    if method != "POST":
        return invalid

    if action[0] == "create":
        try:
            output = create_user(email, passwd)
        except ValueError:
            return invalid
    elif action[0] == "login":
        try:
            output = login(email, passwd)
        except ValueError:
            return invalid

    return {
        'statusCode': 200,
        'body': output
    }

