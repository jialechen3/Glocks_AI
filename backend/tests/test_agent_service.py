import unittest

from fastapi.testclient import TestClient

from backend.agent_models import ActionType, AgentAnalyzeRequest, Intent, RiskLevel
from backend.agent_service import analyze_request
from backend.main import app
from backend.models import PreparedEmail


class AgentServiceTests(unittest.TestCase):
    def test_organize_inbox_classifies_work_promotions_and_newsletters(self) -> None:
        request = AgentAnalyzeRequest(
            user_command="Organize my inbox into labels.",
            emails=[
                PreparedEmail(
                    message_id="work-1",
                    from_address="Manager <manager@company.com>",
                    subject="Team sync moved to 4pm",
                    snippet="Please review the agenda before the meeting.",
                    body_text="The client meeting is now at 4pm.",
                ),
                PreparedEmail(
                    message_id="promo-1",
                    from_address="deals@shopnow.com",
                    subject="Limited time sale",
                    snippet="Save big on your next order.",
                    body_text="Use this coupon for free shipping.",
                ),
                PreparedEmail(
                    message_id="news-1",
                    from_address="weekly@updates.example",
                    subject="Weekly digest",
                    snippet="Top stories this week.",
                    body_text="Manage preferences or unsubscribe here.",
                ),
            ],
        )

        response = analyze_request(request)

        self.assertEqual(response.intent, Intent.ORGANIZE_INBOX)
        self.assertTrue(response.needs_confirmation)
        self.assertEqual(response.risk_level, RiskLevel.MEDIUM)
        self.assertEqual(len(response.groups), 3)
        self.assertEqual(
            [action.label_name for action in response.suggested_actions],
            ["Work", "Promotions", "Newsletters"],
        )
        self.assertTrue(all(action.action_type == ActionType.APPLY_LABEL for action in response.suggested_actions))

    def test_delete_request_uses_high_risk_trash_actions(self) -> None:
        request = AgentAnalyzeRequest(
            user_command="Delete the low priority promo emails.",
            emails=[
                PreparedEmail(
                    message_id="promo-1",
                    from_address="offers@brand.com",
                    subject="Discount offer just for you",
                    snippet="Limited time deal",
                    body_text="Shop now and save big.",
                ),
                PreparedEmail(
                    message_id="news-1",
                    from_address="newsletter@example.com",
                    subject="Daily digest",
                    snippet="Your morning briefing",
                    body_text="Unsubscribe from this newsletter anytime.",
                ),
            ],
        )

        response = analyze_request(request)

        self.assertEqual(response.intent, Intent.DELETE_EMAILS)
        self.assertTrue(response.needs_confirmation)
        self.assertEqual(response.risk_level, RiskLevel.HIGH)
        self.assertEqual(len(response.suggested_actions), 1)
        self.assertEqual(response.suggested_actions[0].action_type, ActionType.TRASH)
        self.assertEqual(
            response.suggested_actions[0].target_message_ids,
            ["promo-1", "news-1"],
        )

    def test_high_risk_request_without_confident_match_flags_for_review(self) -> None:
        request = AgentAnalyzeRequest(
            user_command="Delete these emails.",
            emails=[
                PreparedEmail(
                    message_id="personal-1",
                    from_address="friend@gmail.com",
                    subject="Dinner plans",
                    snippet="Are we still on for tonight?",
                    body_text="Let me know if 7 works for you.",
                )
            ],
        )

        response = analyze_request(request)

        self.assertEqual(response.risk_level, RiskLevel.HIGH)
        self.assertEqual(response.suggested_actions[0].action_type, ActionType.FLAG_FOR_REVIEW)
        self.assertIn("reviewed", response.warnings[0].lower())


class AgentEndpointTests(unittest.TestCase):
    def test_analyze_endpoint_returns_structured_response(self) -> None:
        client = TestClient(app)

        response = client.post(
            "/api/agent/analyze",
            json={
                "user_command": "Find newsletters in my inbox.",
                "emails": [
                    {
                        "message_id": "n-1",
                        "from_address": "digest@example.com",
                        "subject": "Weekly digest",
                        "snippet": "Top links this week",
                        "body_text": "Unsubscribe or manage preferences anytime.",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "find_newsletters")
        self.assertEqual(payload["risk_level"], "low")
        self.assertEqual(payload["groups"][0]["group_name"], "Newsletters")


if __name__ == "__main__":
    unittest.main()
