import json
import os
import uuid

import boto3
from botocore.config import Config
from jsonschema import validate

import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from parameter_util import ParameterUtil
from user_util import UserUtil


class MeArticlesImageUploadUrlShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'upload_image_size': settings.parameters['upload_image_size'],
                'upload_image_extension': settings.parameters['upload_image_extension']
            },
            'required': ['article_id', 'upload_image_size', 'upload_image_extension']
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema())
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.event['pathParameters']['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username']
        )

    def exec_main_proc(self):
        s3_cli = boto3.client('s3', config=Config(signature_version='s3v4'), region_name='ap-northeast-1')
        bucket = os.environ['DIST_S3_BUCKET_NAME']

        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        file_name = str(uuid.uuid4()) + '.' + self.params['upload_image_extension']
        key = settings.S3_ARTICLES_IMAGES_PATH + user_id + '/' + self.params['article_id'] + '/' + file_name

        content_length = self.params['upload_image_size']

        upload_url = s3_cli.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': bucket, 'Key': key, 'ContentLength': content_length},
            ExpiresIn=300,
            HttpMethod='PUT'
        )

        show_url = 'https://' + os.environ['DOMAIN'] +\
            '/d/api/articles_images/' + user_id + '/' + self.params['article_id'] + '/' + file_name

        return {
            'statusCode': 200,
            'body': json.dumps({
                'show_url': show_url,
                'upload_url': upload_url
            })
        }
