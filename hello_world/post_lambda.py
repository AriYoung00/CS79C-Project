import json
import boto3
import uuid

from passlib.hash import pbkdf2_sha256

USERS_TABLE_NAME = "FinalProjUsers"
POSTS_TABLE_NAME = "FinalProjPosts"
NO_SUCCESS = {'success': False}

db = None


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


def create_post(title, body_text, user_id):
    if not (title and body_text and user_id):
        raise ValueError("Invalid arguments to create_post")

    # Not filtering for duplicate posts because that makes no sense to me
    post_id = uuid.uuid1()
    db.put_item(
        Table=POSTS_TABLE_NAME,
        Item={
            'post_id': post_id,
            'title': title,
            'body_text': body_text,
            'users_uvote': [user_id],
            'users_dvote': []
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
    invalid2 = {
        'statusCode': 403,
        'body': "ddfgsdfhrtj"
    }

    # try:
    #     action = event['pathParameters']['action'].split('/')
    #     method = event['httpMethod']
    #     body = json.loads(event["body"])
    #     user_id = body['uuid']
    #     post_id = body['post_id']
    #     token = body['token']
    # except KeyError:
    #     return invalid2

    action = event['pathParameters']['action'].split('/')
    method = event['httpMethod']
    body = json.loads(event["body"])
    user_id = body['uuid']
    token = body['token']

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

        try:
            output = create_post(body["title"], body["body_text"], body["uuid"])
        except KeyError or ValueError:
            return invalid

    return {
        'statusCode': 200,
        'body': output
    }
