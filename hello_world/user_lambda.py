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
    # Check if user email is already taken
    resp = db.get_item(
        TableName=USERS_TABLE_NAME,
        Key={
            'email': {'S': email}
        }
    )
    if resp['items']:
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
        'uuid': user_id,
        'email': email,
        'pwd_hash': pwd_hash,
        'session_secret': session_secret,
        'expire_time': token_expire_time
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
dict containing success value, uuid, session token

"""


def login(email, passwd):
    if not email or not passwd:
        raise ValueError("Email or password not given")

    resp = db.get_item(
        TableName=USERS_TABLE_NAME,
        Key={
            'email': email
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


def verify_session(uuid, token):
    resp = db.get_item(
        TableName=USERS_TABLE_NAME,
        Key={
            'uuid': uuid
        }
    )
    item = resp['Item']
    # Fail if user does not exist
    if not item:
        return False

    return pbkdf2_sha256.verify(item['session_secret'], token)


def lambda_handler(event, context):
    malformed = {
        'statusCode': 400,
        'body': "Malformed request"
    }

    global db
    db = boto3.client("dynamodb")
    action = None
    method = None

    try:
        action = event['pathParameters']['action'].split('/')
        method = event['httpMethod']
    except KeyError:
        return malformed

    if method != "POST":
        return {
            'statusCode': 403,
            'body': "Invalid protocol"
        }

    if action[0] == "add":
        body = None
        try:
            body = json.loads(event["body"])
        except:
            return malformed

        try:
            result

