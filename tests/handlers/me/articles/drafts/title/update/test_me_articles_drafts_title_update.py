import json
import os
from unittest import TestCase
from me_articles_drafts_title_update import MeArticlesDraftsTitleUpdate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesDraftsTitleUpdate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

    def setUp(self):
        TestsUtil.delete_all_tables(self.dynamodb)

        self.article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        self.article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_info_items = [
            {
                'article_id': 'draftId00001',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'version': 2
            },
            {
                'article_id': 'publicId0001',
                'user_id': 'test01',
                'status': 'public',
                'sort_key': 1520150272000000,
                'version': 2
            },
            {
                'article_id': 'draftId00002',
                'user_id': 'test02',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'version': 2
            },
            {
                'article_id': 'draftId00003',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'version': 2
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        article_content_items = [
            {
                'article_id': 'draftId00001',
                'title': 'sample_title1',
                'body': 'sample_body1'
            },
            {
                'article_id': 'publicId0002',
                'title': 'sample_title2',
                'body': 'sample_body2'
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], article_content_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        me_articles_drafts_title_update = MeArticlesDraftsTitleUpdate(params, {}, self.dynamodb)
        response = me_articles_drafts_title_update.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'title': 'update title'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        me_articles_drafts_update = MeArticlesDraftsTitleUpdate(params, {}, self.dynamodb)

        response = me_articles_drafts_update.main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_info_after[0]['user_id'])

        for key, value in json.loads(params['body']).items():
            self.assertEqual(value, article_info_after[0][key])
            self.assertEqual(value, article_content_after[0][key])

    def test_main_ok_with_empty_string(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'title': ''
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        response = MeArticlesDraftsTitleUpdate(params, {}, self.dynamodb).main()
        article_info = self.article_info_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        article_content = self.article_content_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(article_info['title'], None)
        self.assertEqual(article_content['title'], None)

    def test_main_ok_article_content_not_exists(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00003'
            },
            'body': {
                'title': 'A' * 255
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        me_articles_drafts_update = MeArticlesDraftsTitleUpdate(params, {}, self.dynamodb)

        response = me_articles_drafts_update.main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 1)

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_info_after[0]['user_id'])

        for key, value in json.loads(params['body']).items():
            target_info = [info for info in article_info_after if info['article_id'] == 'draftId00003'][0]
            self.assertEqual(value, target_info[key])
            target_content = [content for content in article_content_after if content['article_id'] == 'draftId00003'][0]
            self.assertEqual(value, target_content[key])

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'eye_catch_url': 'http://example.com/update',
                'title': 'update title'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_articles_drafts_title_update.DBUtil', mock_lib):
            MeArticlesDraftsTitleUpdate(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['user_id'])
            self.assertEqual(kwargs['status'], 'draft')
            self.assertEqual(kwargs['version'], 2)

    def test_call_sanitize_text(self):
        title_str = 'test_title'
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'title': title_str
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_articles_drafts_title_update.TextSanitizer', mock_lib):
            MeArticlesDraftsTitleUpdate(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.sanitize_text.call_args
            self.assertTrue(mock_lib.sanitize_text.called)
            self.assertEqual(args[0], title_str)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_with_no_body_params(self):
        params = {
            'body': {},
            'pathParameters': {
                'article_id': 'A' * 12
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_with_no_path_params(self):
        params = {
            'body': {
                'title': 'A' * 200
            },
            'pathParameters': {}
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_title_max(self):
        params = {
            'body': {
                'title': 'A' * 256
            },
            'pathParameters': {
                'article_id': 'A' * 12
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'body': {
                'title': 'A' * 50
            },
            'pathParameters': {
                'article_id': 'A' * 13
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'body': {
                'title': 'A' * 50
            },
            'pathParameters': {
                'article_id': 'A' * 11
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)
