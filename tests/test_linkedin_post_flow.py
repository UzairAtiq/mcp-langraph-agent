from starlette.testclient import TestClient
from api.main import app
from data.post_storage import (
    generate_next_post_id,
    save_post_record,
    get_post_by_id,
    update_post_status,
)
from services.slack_service import build_approval_blocks

# test storage functions
def test_storage_lifecycle():
    # generate a unique test post id
    post_id = generate_next_post_id()
    assert post_id.startswith("post_")

    # save post record
    record = save_post_record(
        post_id=post_id,
        content="Excited to share insights on AI agents!",
        profile_id="urn:li:person:test_user_123",
        access_token="test_token_xyz",
        status="pending",
    )
    assert record["post_id"] == post_id
    assert record["status"] == "pending"

    # fetch record by id
    fetched = get_post_by_id(post_id)
    assert fetched is not None
    assert fetched["content"] == "Excited to share insights on AI agents!"

    # update status to published
    updated = update_post_status(post_id, "published", extra_data={"urn": "urn:li:share:999"})
    assert updated["status"] == "published"
    assert updated["urn"] == "urn:li:share:999"

# test slack block kit structure
def test_slack_block_structure():
    post_id = "post_100_abc"
    content = "Sample LinkedIn post body"
    blocks = build_approval_blocks(post_id=post_id, content=content)

    assert len(blocks) == 4
    # verify action block contains approve and discard buttons
    action_block = blocks[3]
    assert action_block["type"] == "actions"
    elements = action_block["elements"]
    assert len(elements) == 2

    approve_button = elements[0]
    assert approve_button["action_id"] == "approve_linkedin_post"
    assert approve_button["value"] == post_id

    discard_button = elements[1]
    assert discard_button["action_id"] == "discard_linkedin_post"
    assert discard_button["value"] == post_id

# test api health and posts endpoints
def test_api_endpoints():
    client = TestClient(app)

    # health check
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json() == {"status": "healthy"}

    # get posts
    posts_res = client.get("/posts")
    assert posts_res.status_code == 200
    data = posts_res.json()
    assert "total_count" in data
    assert "posts" in data
