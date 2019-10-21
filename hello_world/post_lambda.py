import json
import boto3
import uuid
import random

from passlib.hash import pbkdf2_sha256
from boto3.dynamodb.conditions import Key, Attr

USERS_TABLE_NAME = "FinalProjUser"
POSTS_TABLE_NAME = "FinalProjPosts"
NO_SUCCESS = {'success': False}

db = None


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


def create_post(title, body_text, user_id):
    if not (title and body_text and user_id):
        raise ValueError("Invalid arguments to create_post")

    # Not filtering for duplicate posts because that makes no sense to me
    post_id = str(uuid.uuid1())
    db.put_item(
        TableName=POSTS_TABLE_NAME,
        Item={
            'upid': {"S": post_id},
            'title': {"S": title},
            'body_text': {"S": body_text},
            'users_uvote': {"SS": [user_id, "phantom-user"]},
            'users_dvote': {"SS": ["phantom-user"]} # Since dynamo does not allow empty string sets
        }
    )

    return {"success": True}


def vote(user_id, upid, vote_type):
    if not (user_id and upid and (not vote_type is None)):
        raise ValueError("Invalid arguments to vote")

    type1 = "users_upvote" if vote_type else "users_downvote"
    type2 = "users_downvote" if vote_type else "users_upvote"

    resp = db.get_item(
        Table=POSTS_TABLE_NAME,
        Key={
            'post_id': upid
        }
    )
    item = resp['Item']
    if not item:
        return NO_SUCCESS

    # Remove opposite vote, if it's there
    if user_id in item[type2]:
        item[type2].remove(user_id)
    # If we've already cast a vote of this type, remove it
    if user_id in item[type1]:
        item[type1].remove(user_id)
    # Else, cast a vote of this type
    else:
        item[type1].append(user_id)

    # Just overwrite
    db.put_item(Table=POSTS_TABLE_NAME, Item=item)
    return {'success': True}


def get_post():
    post = random.choice(db.scan(TableName=POSTS_TABLE_NAME)["Items"])
    return {
        'success': True,
        'upid': post['upid']['S'],
        'title': post['title']['S'],
        'body': post['body_text']['S'],
        'score': len(post['users_uvote']['SS']) - len(post['users_dvote']['SS'])
    }


def lambda_handler(event, context):
    global db
    db = boto3.client("dynamodb")

    action = None
    method = None
    body = None
    invalid = {
        'statusCode': 403,
        'body': "Invalid protocol"
    }

    try:
        action = event['pathParameters']['action'].split('/')
        method = event['httpMethod']
        body = json.loads(event["body"])
        user_id = body['user_id']
        token = body['token']
    except KeyError:
        return invalid

    if method != "POST":
        return invalid

    if not verify_session(user_id, token):
        return {
            'statusCode': 503,
            'body': "Forbidden"
        }

    output = None
    if action[0] == "vote":
        try:
            post_id = body['post_id']
            output = vote(user_id, post_id, body["vote_type"])
        except KeyError or ValueError:
            return invalid
    elif action[0] == "create":
        if "title" not in body or "body_text" not in body:
            return invalid

        # try:
        #     output = create_post(body["title"], body["body_text"], body["uuid"])
        # except KeyError or ValueError:
        #     return invalid

        output = create_post(body["title"], body["body_text"], body["user_id"])
    elif action[0] == "get":
        output = get_post()

    return {
        'statusCode': 200,
        'body': json.dumps(output)
    }
