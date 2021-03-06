import os
import boto3
import base64
import json
import settings
from tests_util import TestsUtil
from unittest import TestCase
from me_articles_images_create import MeArticlesImagesCreate
from unittest.mock import patch, MagicMock
from PIL import Image
from io import BytesIO
import tempfile


class TestMeArticlesImagesCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()
    s3 = boto3.resource('s3', endpoint_url='http://localhost:4572/')

    @classmethod
    def setUpClass(cls):
        os.environ['DOMAIN'] = 'example.com'
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.set_all_s3_buckets_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create s3 bucket
        TestsUtil.create_all_s3_buckets(cls.s3)

        # create article_info_table
        cls.article_info_table_items = [
            {
                'article_id': 'testid000000',
                'status': 'public',
                'user_id': 'test0000',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'status': 'draft',
                'user_id': 'test0001',
                'sort_key': 1520150272000001
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], cls.article_info_table_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        test_function = MeArticlesImagesCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    def equal_size_to_s3_image(self, s3_key, target_image_size):
        bucket = self.s3.Bucket(os.environ['DIST_S3_BUCKET_NAME'])
        image_tmp = tempfile.NamedTemporaryFile()

        with open(image_tmp.name, 'wb') as f:
            bucket.download_file(s3_key, f.name)
            download_image_data = Image.open(image_tmp.name, 'r')
            if download_image_data.size == target_image_size:
                return True
        return False

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_status_public(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesImagesCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        self.assertEqual(response['statusCode'], 200)

        image_url_path = target_article_info['user_id'] + '/' + target_article_info['article_id'] + '/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_ARTICLES_IMAGES_PATH + image_url_path + image_file_name
        expected_item = {
            'image_url': 'https://' + os.environ['DOMAIN'] + '/' + key
        }
        self.assertEqual(json.loads(response['body']), expected_item)
        self.assertTrue(self.equal_size_to_s3_image(key, image_data.size))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_status_draft_and_content_type_is_upper_case(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[1]
        params = {
            'headers': {
                    'Content-Type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesImagesCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        self.assertEqual(response['statusCode'], 200)

        image_url_path = target_article_info['user_id'] + '/' + target_article_info['article_id'] + '/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_ARTICLES_IMAGES_PATH + image_url_path + image_file_name
        expected_item = {
            'image_url': 'https://' + os.environ['DOMAIN'] + '/' + key
        }
        self.assertEqual(json.loads(response['body']), expected_item)
        self.assertTrue(self.equal_size_to_s3_image(key, image_data.size))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_width_over_png(self):
        image_data = Image.new('RGB', (settings.ARTICLE_IMAGE_MAX_WIDTH + 1, settings.ARTICLE_IMAGE_MAX_HEIGHT))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                    'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesImagesCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        self.assertEqual(response['statusCode'], 200)

        image_url_path = target_article_info['user_id'] + '/' + target_article_info['article_id'] + '/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_ARTICLES_IMAGES_PATH + image_url_path + image_file_name
        expected_item = {
            'image_url': 'https://' + os.environ['DOMAIN'] + '/' + key
        }
        self.assertEqual(json.loads(response['body']), expected_item)
        self.assertTrue(self.equal_size_to_s3_image(key, (3840, 2159)))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_height_over_gif(self):
        image_data = Image.new('RGB', (settings.ARTICLE_IMAGE_MAX_WIDTH, settings.ARTICLE_IMAGE_MAX_HEIGHT + 1))
        buf = BytesIO()
        image_format = 'gif'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesImagesCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        self.assertEqual(response['statusCode'], 200)

        image_url_path = target_article_info['user_id'] + '/' + target_article_info['article_id'] + '/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_ARTICLES_IMAGES_PATH + image_url_path + image_file_name
        expected_item = {
            'image_url':  'https://' + os.environ['DOMAIN'] + '/' + key
        }
        self.assertEqual(json.loads(response['body']), expected_item)
        self.assertTrue(self.equal_size_to_s3_image(key, (3838, 2160)))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_max_size_jepg(self):
        image_data = Image.new('RGB', (settings.ARTICLE_IMAGE_MAX_WIDTH, settings.ARTICLE_IMAGE_MAX_HEIGHT))
        buf = BytesIO()
        image_format = 'jpeg'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                    'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesImagesCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        self.assertEqual(response['statusCode'], 200)

        image_url_path = target_article_info['user_id'] + '/' + target_article_info['article_id'] + '/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_ARTICLES_IMAGES_PATH + image_url_path + image_file_name
        expected_item = {
            'image_url': 'https://' + os.environ['DOMAIN'] + '/' + key
        }
        self.assertEqual(json.loads(response['body']), expected_item)
        self.assertTrue(self.equal_size_to_s3_image(key, image_data.size))

    def test_validation_with_no_params(self):
        params = {
        }

        self.assert_bad_request(params)

    def test_validation_with_no_content_type(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_with_no_article_id(self):
        image_data = Image.new('RGB', (settings.ARTICLE_IMAGE_MAX_WIDTH, settings.ARTICLE_IMAGE_MAX_HEIGHT))
        buf = BytesIO()
        image_format = 'jpeg'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'pathParameters': {
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_with_no_article_image(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_with_no_supported_content_type(self):
        image_data = Image.new('RGB', (settings.ARTICLE_IMAGE_MAX_WIDTH, settings.ARTICLE_IMAGE_MAX_HEIGHT))
        buf = BytesIO()
        image_format = 'jpeg'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/bmp'
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        image_data = Image.new('RGB', (settings.ARTICLE_IMAGE_MAX_WIDTH, settings.ARTICLE_IMAGE_MAX_HEIGHT))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': 'a' * 13
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        image_data = Image.new('RGB', (settings.ARTICLE_IMAGE_MAX_WIDTH, settings.ARTICLE_IMAGE_MAX_HEIGHT))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': 'a' * 11
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_article_image_not_image_format(self):
        image_format = 'png'

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                    'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': 'a' * (1024 * 1024 * 8)}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'another-user',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_article_image_over_data_size(self):
        image_format = 'png'
        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                    'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': 'a' * (settings.parameters['article_image']['maxLength'] + 1)}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        response = MeArticlesImagesCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertRegex(response['body'], 'Invalid parameter')

    def test_validation_article_image_empty(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                    'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': ''}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_call_validate_article_existence(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_article_info = self.article_info_table_items[0]
        params = {
            'headers': {
                    'content-type': 'image/' + image_format
            },
            'pathParameters': {
                'article_id': target_article_info['article_id']
            },
            'body': json.dumps({'article_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_article_info['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_images_create.DBUtil', mock_lib):
            MeArticlesImagesCreate(params, {}, self.dynamodb, self.s3).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['user_id'])
