from bedrock_agentcore_starter_toolkit import Runtime
import os
from dotenv import load_dotenv

load_dotenv()

def deploy_tech_learning_assistant():
    print("🚀 エージェントをデプロイ中...")

    env_vars = {
        # "MEMORY_ID": os.getenv("MEMORY_ID"),
        "REGION": os.getenv("REGION", "us-west-2"),
    }

    runtime = Runtime()

    # 環境変数からIAMロールARNを取得
    execution_role = os.getenv("EXECUTION_ROLE_ARN")
    if not execution_role:
        raise ValueError("EXECUTION_ROLE_ARN環境変数が設定されていません")

    response = runtime.configure(
        entrypoint="my_agent.py",
        execution_role=execution_role,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region="us-west-2",
        agent_name=os.getenv("AGENT_NAME", "my_agent_toolkit")
    )

    print("✅ 設定完了！デプロイを実行中...")

    launch_result = runtime.launch(env_vars=env_vars)

    print(f"✅ デプロイ完了！")

    # Agent Runtime ARNを取得して.envファイルを自動更新
    try:
        # launch_resultからAgent Runtime ARNを抽出
        agent_runtime_arn = None

        if hasattr(launch_result, 'agent_arn'):
            agent_runtime_arn = launch_result.agent_arn
        elif isinstance(launch_result, dict):
            agent_runtime_arn = launch_result.get('agent_arn')

        if agent_runtime_arn:
            print(f"🔗 Agent Runtime ARN: {agent_runtime_arn}")

            # .envファイルを自動で更新
            try:
                with open('.env', 'r') as f:
                    content = f.read()

                # AGENT_RUNTIME_ARNの行を更新
                lines = content.split('\n')
                updated_lines = []
                arn_updated = False

                for line in lines:
                    if line.startswith('AGENT_RUNTIME_ARN='):
                        updated_lines.append(f'AGENT_RUNTIME_ARN={agent_runtime_arn}')
                        arn_updated = True
                        print(f"✅ .envファイルのAGENT_RUNTIME_ARNを更新しました")
                    else:
                        updated_lines.append(line)

                # もしAGENT_RUNTIME_ARNの行がない場合は追加
                if not arn_updated:
                    updated_lines.append(f'AGENT_RUNTIME_ARN={agent_runtime_arn}')
                    print(f"✅ .envファイルにAGENT_RUNTIME_ARNを追加しました")

                with open('.env', 'w') as f:
                    f.write('\n'.join(updated_lines))
                    if not content.endswith('\n'):
                        f.write('\n')

                print(f"🎉 .envファイルを自動更新しました！")

            except Exception as e:
                print(f"⚠️ .envファイルの更新に失敗しました: {e}")
                print(f"手動で以下をAGENT_RUNTIME_ARNに設定してください: {agent_runtime_arn}")
        else:
            print(f"⚠️ Agent Runtime ARNを取得できませんでした")
            print(f"デプロイ結果: {launch_result}")
            print("手動でAGENT_RUNTIME_ARNを.envファイルに設定してください")

    except Exception as e:
        print(f"⚠️ Agent Runtime ARN取得エラー: {e}")
        print(f"デプロイ結果: {launch_result}")

    return launch_result

if __name__ == "__main__":
    deploy_tech_learning_assistant()
