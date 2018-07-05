#!/usr/bin/env bash

target=
if [ $1 ] ; then
  target="${1}-"
else
  echo "You have to specify the target to deployment."
  exit 1
fi

# SSMに登録するパラメータは、ALIS_APP_IDを含めた値がPrefixとして定義される
# See: https://github.com/AlisProject/environment
SSM_PARAMS_PREFIX=${ALIS_APP_ID}ssm

DEPLOY_BUCKET_NAME=${ALIS_APP_ID}-serverless-deploy-bucket

aws cloudformation package \
  --template-file ${target}template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --output-template-file ${target}packaged-template.yaml

aws cloudformation deploy \
  --template-file ${target}packaged-template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --stack-name ${ALIS_APP_ID}${1} \
  --parameter-overrides \
    AlisAppDomain=${SSM_PARAMS_PREFIX}AlisAppDomain \
    PrivateChainAwsAccessKey=${SSM_PARAMS_PREFIX}PrivateChainAwsAccessKey \
    PrivateChainAwsSecretAccessKey=${SSM_PARAMS_PREFIX}PrivateChainAwsSecretAccessKey \
    PrivateChainExecuteApiHost=${SSM_PARAMS_PREFIX}PrivateChainExecuteApiHost \
    BetaModeFlag=${SSM_PARAMS_PREFIX}BetaModeFlag \
    SaltForArticleId=${SSM_PARAMS_PREFIX}SaltForArticleId \
    CognitoUserPoolArn=${SSM_PARAMS_PREFIX}CognitoUserPoolArn \
    ArticleInfoTableName=${SSM_PARAMS_PREFIX}ArticleInfoTableName \
    ArticleContentTableName=${SSM_PARAMS_PREFIX}ArticleContentTableName \
    ArticleHistoryTableName=${SSM_PARAMS_PREFIX}ArticleHistoryTableName \
    ArticleContentEditTableName=${SSM_PARAMS_PREFIX}ArticleContentEditTableName \
    ArticleEvaluatedManageTableName=${SSM_PARAMS_PREFIX}ArticleEvaluatedManageTableName \
    ArticleAlisTokenTableName=${SSM_PARAMS_PREFIX}ArticleAlisTokenTableName \
    ArticleLikedUserTableName=${SSM_PARAMS_PREFIX}ArticleLikedUserTableName \
    ArticleFraudUserTableName=${SSM_PARAMS_PREFIX}ArticleFraudUserTableName \
    ArticlePvUserTableName=${SSM_PARAMS_PREFIX}ArticlePvUserTableName \
    ArticleScoreTableName=${SSM_PARAMS_PREFIX}ArticleScoreTableName \
    UsersTableName=${SSM_PARAMS_PREFIX}UsersTableName \
    BetaUsersTableName=${SSM_PARAMS_PREFIX}BetaUsersTableName \
    NotificationTableName=${SSM_PARAMS_PREFIX}NotificationTableName \
    UnreadNotificationManagerTableName=${SSM_PARAMS_PREFIX}UnreadNotificationManagerTableName \
    DistS3BucketName=${SSM_PARAMS_PREFIX}DistS3BucketName \
  --capabilities CAPABILITY_IAM