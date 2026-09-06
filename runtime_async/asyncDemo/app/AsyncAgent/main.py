"""非同期 / 長時間実行エージェントのサンプル (AgentCore Runtime)。

参考: https://zenn.dev/aws_japan/articles/agentcore-async-long-running-patterns

ポイント:
  - entrypoint は即座にレスポンスを返す (15 分の Request timeout に抵触しない)。
  - add_async_task() でセッションを Active (HealthyBusy) にし、バックグラウンドで
    長時間処理を継続する。処理中は /ping が HealthyBusy を返し、アイドルタイムアウト
    (idleRuntimeSessionTimeout) を回避して実行環境を維持する。
  - complete_async_task() でカウンタを戻すと /ping が Healthy に戻り、実行環境は
    通常のアイドルタイムアウトで回収される (= 環境を維持しない)。

このサンプルはストリーミングを使わない。entrypoint は通常の async 関数として
辞書を返し、SDK が JSON レスポンスとして返す。
"""

import asyncio
from typing import Any, Dict

from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp, PingStatus

# BedrockAgentCoreApp が /ping と /invocations のルーティングを管理する
app = BedrockAgentCoreApp()
log = app.logger

SYSTEM_PROMPT = "You are a helpful assistant. Use tools when appropriate."


# シンプルな関数ツール
@tool
def add_numbers(a: int, b: int) -> int:
    """Return the sum of two numbers"""
    return a + b


# エージェントは 1 つだけ用意する (サンプルなのでセッションごとの分離はしない)
agent = Agent(
    model=BedrockModel(model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    system_prompt=SYSTEM_PROMPT,
    tools=[add_numbers],
)


@app.ping
def health_check() -> PingStatus:
    """ヘルスチェック。

    アクティブなバックグラウンドタスクがあれば HealthyBusy を返し、実行環境の
    アイドルタイムアウトを回避する。タスクが無ければ Healthy を返す。
    """
    active = app.get_async_task_info()["active_count"]
    status = PingStatus.HEALTHY_BUSY if active > 0 else PingStatus.HEALTHY
    log.info(f"Ping: status={status.value}, active_tasks={active}")
    return status


async def _background_run(task_id: int, prompt: str, duration: int):
    """バックグラウンドで長時間処理を行うコルーチン。

    duration > 0 の場合、その秒数だけ asyncio.sleep で意図的に待機し、長時間実行を
    シミュレートする (60 秒ごとに経過ログを出力)。その後にエージェントを実行する。

    try/finally で complete_async_task() を必ず呼ぶ。呼び忘れると HealthyBusy が
    永続し、maxLifetime に達するまで実行環境が終了せず課金が続く。
    """
    try:
        log.info(f"[Background] task_id={task_id} | start (duration={duration}s)")

        # --- 意図的な遅延 (長時間実行のシミュレーション) ---
        elapsed = 0
        while elapsed < duration:
            step = min(60, duration - elapsed)
            await asyncio.sleep(step)
            elapsed += step
            log.info(f"[Background] task_id={task_id} | elapsed={elapsed}s / {duration}s")

        # --- エージェント実行 (Strands の呼び出しは同期 API なのでスレッドへ) ---
        response = await asyncio.to_thread(agent, prompt)
        result = response.message["content"][0]["text"]
        log.info(f"[Background] task_id={task_id} | completed: {str(result)[:200]}")
    except Exception as e:
        log.exception(f"[Background] task_id={task_id} | failed: {e}")
    finally:
        # 必ず呼ぶ (HealthyBusy を解除して実行環境をアイドルに戻す)
        app.complete_async_task(task_id)


@app.entrypoint
async def invoke(payload: Dict[str, Any], context=None):
    """エントリーポイント。

    - action="start"  : 非同期ジョブを開始し、即座に status を返す (環境を維持)。
    - action="status" : 実行中の非同期ジョブ (active_count / running_jobs) を返す。
    """
    # payload から action を取り出す (payload が dict でなければ None として扱う)
    action = payload.get("action") if isinstance(payload, dict) else None
    log.info(f"[Entrypoint] action={action}")

    # --- 状態確認: 実行中の非同期ジョブを返す ---
    if action == "status":
        # get_async_task_info() は SDK が管理する現在のタスク状態を返す。
        #   - active_count: 実行中の非同期タスク数。1 以上なら HealthyBusy 維持中。
        #   - running_jobs: 実行中タスクの一覧。各要素は
        #       name     (add_async_task で付けた名前。ここでは "long_job")
        #       duration (タスク開始からの経過秒数)
        #     を持つ。
        # 例: {"active_count": 1, "running_jobs": [{"name": "long_job", "duration": 3.5}]}
        return app.get_async_task_info()

    # --- ジョブ開始: 非同期タスクを登録し、即座に応答を返す ---
    if action == "start":
        prompt = payload.get("prompt", "")
        
        # duration (意図的な遅延秒数) を安全に int 化する。
        # 未指定・不正値・負値はすべて 0 (遅延なし) に丸める。
        duration = payload.get("duration", 0)
        try:
            duration = max(0, int(duration))
        except (TypeError, ValueError):
            duration = 0

        # add_async_task でタスクを登録 -> /ping が HealthyBusy を返すようになる。
        task_id = app.add_async_task("long_job", {"duration": duration})
        
        # create_task でバックグラウンド処理を起動する。await しないので、
        # 処理完了を待たずに次の return まで進む。
        asyncio.create_task(_background_run(task_id, prompt, duration))
        log.info(f"[Entrypoint] started async task_id={task_id} duration={duration}s")
        
        # 即座に応答を返す (バックグラウンド処理は継続する)。
        return {"status": "started", "task_id": task_id, "duration": duration}

    # --- 未知の action: 使い方のヒントを返す ---
    return {"error": "unknown action", "hint": "use action='start' or action='status'"}


if __name__ == "__main__":
    app.run()
