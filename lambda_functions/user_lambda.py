import json
import boto3
import uuid
import secrets
import datetime

from passlib.hash import pbkdf2_sha256

USERS_TABLE_NAME = "FinalProjUser"
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
    items = resp.get('Items')
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
        'user_id': {"S": user_id},
        'email': {"S": email},
        'pwd_hash': {"S": pwd_hash},
        'session_secret': {"S": session_secret},
        'expire_time': {"S": token_expire_time}
    })

    return {
        'success': True,
        'user_id': user_id,
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
    item = resp.get('Items')[0]
    # Fail if user does not exist
    if not item:
        return NO_SUCCESS

    # Fail if verification fails
    if not pbkdf2_sha256.verify(passwd, item['pwd_hash']["S"]):
        return NO_SUCCESS

    # Create new session secret, hash, expire time
    session_secret = secrets.token_urlsafe(16)
    session_hash = pbkdf2_sha256.hash(session_secret)
    token_expire_time = str(datetime.datetime.now() + datetime.timedelta(days=7))

    item['session_secret']["S"] = session_secret
    item['expire_time']['S'] = token_expire_time

    db.put_item(TableName=USERS_TABLE_NAME, Item=item)

    return {
        'success': True,
        'user_id': item['user_id'],
        'token': session_hash
    }


def verify_session(user_id, token):
    resp = db.query(
        TableName=USERS_TABLE_NAME,
        IndexName="user_id-index",
        ExpressionAttributeValues={
            ':v': {
                'S': user_id
            }
        },
        KeyConditionExpression='user_id = :v'
    )
    items = resp.get('Items')
    # Fail if user does not exist
    if not items:
        return False

    return pbkdf2_sha256.verify(items[0]['session_secret']['S'], token)


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
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': "Invalid protocol"
    }


    try:
        action = event['pathParameters']['action'].split('/')
        method = event['httpMethod']
        body = json.loads(event["body"])
    except:
        return invalid

    invalid2 = {
        'statusCode': 403,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': "ASDASDFADFADFS"
    }

    if method != "POST":
        return invalid2

    if action[0] == "create":
        try:
            output = create_user(body['email'], body['password'])
        except ValueError:
            return invalid
    elif action[0] == "login":
        try:
            output = login(body['email'], body['password'])
        except ValueError:
            return invalid
    elif action[0] == "verify":
        try:
            output = {"success": verify_session(body['user_id'], body['token'])}
        except:
            return invalid2
    else:
        return invalid

    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(output)
    }

