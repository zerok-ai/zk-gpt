from fastapi import APIRouter, HTTPException

from app.schedulers.issue_inference_generation_scheduler import issue_inference_scheduler_task
from app.schedulers.slack_reporting_scheduler import slack_reporting_scheduler_task
from app.internal.langchain_adapter.langsmith_adapter import LangsmithAdapter
from app.services import internal_demo_service

router = APIRouter()
internal_demo_service_impl = internal_demo_service.InternalDemoService()


@router.post('/v1/c/gpt/clearReporting')
def clear_slack_reporting():
    internal_demo_service_impl.clear_slack_reporting()
    return {"message": "Slack reporting cleared"}, 200


@router.post('/v1/c/gpt/clearAllIssueData')
def clear_all_issue_data():
    internal_demo_service_impl.clear_all_issue_data_for_demo()
    return {"message": "All issue data cleared"}, 200


@router.post('/v1/c/gpt/triggerTask')
def trigger_issue_scheduler_task_manually():
    try:
        # Manually trigger the task here
        issue_inference_scheduler_task()
        return {"message": "Issue scheduler Task triggered successfully"}, 200
    except Exception as e:
        return HTTPException(detail=str(e), status_code=500)


@router.get('/v1/c/gpt/updateLangsmithPush')
def update_langsmith_push_flag(flag: bool):
    try:
        old_flag = LangsmithAdapter.langsmith_push_enabled
        LangsmithAdapter.update_langsmith_push_enabled(flag)
        new_flag = LangsmithAdapter.langsmith_push_enabled
        return {"langsmith_old_flag": old_flag,"langsmith_new_flag": new_flag }, 200
    except Exception as e:
        return HTTPException(detail=str(e), status_code=500)


@router.post('/v1/c/gpt/triggerReporting')
def trigger_slack_reporting_manually():
    try:
        slack_reporting_scheduler_task()  # Manually trigger the task
        return {"message": "Reporting Task triggered successfully."}, 200
    except Exception as e:
        return HTTPException(detail=str(e), status_code=500)

