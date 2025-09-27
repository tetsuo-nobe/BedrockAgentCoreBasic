import boto3
import json
from dotenv import load_dotenv

load_dotenv()

def create_execution_role():
    print("🔐 IAM Execution Roleを作成中...")

    iam = boto3.client('iam', region_name='us-west-2')
    sts = boto3.client('sts', region_name='us-west-2')

    # アカウントIDを動的取得
    account_id = sts.get_caller_identity()['Account']
    region = 'us-west-2'

    # IAM Role名
    role_name = "AgentCoreExecutionRole"

    # Trust policy
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": account_id
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    }
                }
            }
        ]
    }

    # 権限ポリシー（Memory機能用の権限を含む）
    permission_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": ["*"]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": f"arn:aws:logs:{region}:{account_id}:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel*",
                    "bedrock-agentcore:*"
                ],
                "Resource": "*"
            }
        ]
    }

    try:
        # 既存のロールを確認
        try:
            existing_role = iam.get_role(RoleName=role_name)
            print(f"✅ 既存のロールが見つかりました: {role_name}")
            role_arn = existing_role['Role']['Arn']

            # .envファイルを自動で更新
            try:
                with open('.env', 'r') as f:
                    content = f.read()

                # EXECUTION_ROLE_ARNの行を更新
                lines = content.split('\n')
                updated_lines = []
                arn_updated = False

                for line in lines:
                    if line.startswith('EXECUTION_ROLE_ARN='):
                        updated_lines.append(f'EXECUTION_ROLE_ARN={role_arn}')
                        arn_updated = True
                        print(f"✅ .envファイルのEXECUTION_ROLE_ARNを更新しました")
                    else:
                        updated_lines.append(line)

                # もしEXECUTION_ROLE_ARNの行がない場合は追加
                if not arn_updated:
                    updated_lines.append(f'EXECUTION_ROLE_ARN={role_arn}')
                    print(f"✅ .envファイルにEXECUTION_ROLE_ARNを追加しました")

                with open('.env', 'w') as f:
                    f.write('\n'.join(updated_lines))
                    if not content.endswith('\n'):
                        f.write('\n')

                print(f"🎉 .envファイルを自動更新しました！")

            except Exception as e:
                print(f"⚠️ .envファイルの更新に失敗しました: {e}")
                print(f"手動で以下をEXECUTION_ROLE_ARNに設定してください: {role_arn}")

            return role_arn
        except iam.exceptions.NoSuchEntityException:
            pass

        # IAM Roleの作成
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for AgentCore Tech Learning Assistant"
        )

        role_arn = response['Role']['Arn']
        print(f"✅ IAM Role作成完了: {role_name}")

        # ポリシーの作成とアタッチ
        policy_name = "AgentCoreExecutionPolicy"

        try:
            policy_response = iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permission_policy),
                Description="Permissions for AgentCore Tech Learning Assistant"
            )
            policy_arn = policy_response['Policy']['Arn']
            print(f"✅ IAM Policy作成完了: {policy_name}")
        except iam.exceptions.EntityAlreadyExistsException:
            # 既存のポリシーがある場合はARNを取得
            account_id = boto3.client('sts').get_caller_identity()['Account']
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            print(f"✅ 既存のポリシーを使用: {policy_name}")

        # ポリシーをロールにアタッチ
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print(f"✅ ポリシーをロールにアタッチ完了")

        print(f"🎉 IAM Execution Role準備完了！")
        print(f"Role ARN: {role_arn}")

        # .envファイルを自動で更新
        try:
            with open('.env', 'r') as f:
                content = f.read()

            # EXECUTION_ROLE_ARNの行を更新
            lines = content.split('\n')
            updated_lines = []
            arn_updated = False

            for line in lines:
                if line.startswith('EXECUTION_ROLE_ARN='):
                    updated_lines.append(f'EXECUTION_ROLE_ARN={role_arn}')
                    arn_updated = True
                    print(f"✅ .envファイルのEXECUTION_ROLE_ARNを更新しました")
                else:
                    updated_lines.append(line)

            # もしEXECUTION_ROLE_ARNの行がない場合は追加
            if not arn_updated:
                updated_lines.append(f'EXECUTION_ROLE_ARN={role_arn}')
                print(f"✅ .envファイルにEXECUTION_ROLE_ARNを追加しました")

            with open('.env', 'w') as f:
                f.write('\n'.join(updated_lines))
                if not content.endswith('\n'):
                    f.write('\n')

            print(f"🎉 .envファイルを自動更新しました！")

        except Exception as e:
            print(f"⚠️ .envファイルの更新に失敗しました: {e}")
            print(f"手動で以下をEXECUTION_ROLE_ARNに設定してください: {role_arn}")

        return role_arn

    except Exception as e:
        print(f"❌ IAM Role作成エラー: {e}")
        return None

if __name__ == "__main__":
    create_execution_role()
