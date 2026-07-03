import unittest
from unittest import mock

from rfmdataset.data import load_problems
from rfmdataset.evaluation import calc_accuracy, parse_proof_evaluation
from rfmdataset.llm import GPTChatter, InvalidRequestConfigError, MissingCredentialError
from rfmdataset.summary import dataset_summary


class CoreTests(unittest.TestCase):
    def test_dataset_has_200_problems(self) -> None:
        problems = load_problems("data")
        self.assertEqual(
            {level: len(items) for level, items in problems.items()},
            {"ms": 52, "hs": 88, "ug": 60},
        )

    def test_dataset_summary_total(self) -> None:
        self.assertEqual(dataset_summary("data")["total"], 200)

    def test_parse_judge_block(self) -> None:
        text = """
### Error Pattern Analysis
- Transformation Error: 0
- Over Generalization: 0
- Invalid Construction: 0
- Wrong Division: 0
- Circular Reasoning: 0
- Logic Violation: 1
- Hidden Assumption: 0
- Boundary Neglect: 0
- Vague Argument: 0
- Incomplete Proof: 0
- Others: 0

### Overall Correctness
- 0
"""
        parsed = parse_proof_evaluation(text)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["Logic Violation"], 1)
        self.assertEqual(parsed["Overall Correctness"], 0)

    def test_calc_accuracy(self) -> None:
        labels = {
            "ms": [{"Overall Correctness": 1}, {"Overall Correctness": 0}],
            "hs": [{"Overall Correctness": 1}],
            "ug": [],
        }
        self.assertEqual(
            calc_accuracy(labels),
            {"ms": 0.5, "hs": 1.0, "ug": 0.0, "overall": 2 / 3},
        )

    def test_llm_requires_user_supplied_endpoint(self) -> None:
        with self.assertRaises(MissingCredentialError):
            GPTChatter(
                "dummy-model",
                api_key="dummy-key",
                base_url_env="RFM_TEST_BASE_URL_THAT_SHOULD_NOT_EXIST",
            )

    def test_llm_extra_body_comes_from_json_env(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {"RFM_TEST_EXTRA_BODY": '{"thinking":{"type":"disabled"}}'},
            clear=False,
        ):
            client = GPTChatter(
                "dummy-model",
                api_key="dummy-key",
                base_url="https://example.com/v1",
                extra_body_env="RFM_TEST_EXTRA_BODY",
            )
        self.assertEqual(client.extra_body, {"thinking": {"type": "disabled"}})

    def test_llm_extra_body_rejects_invalid_json(self) -> None:
        with mock.patch.dict("os.environ", {"RFM_TEST_EXTRA_BODY": "not-json"}, clear=False):
            with self.assertRaises(InvalidRequestConfigError):
                GPTChatter(
                    "dummy-model",
                    api_key="dummy-key",
                    base_url="https://example.com/v1",
                    extra_body_env="RFM_TEST_EXTRA_BODY",
                )


if __name__ == "__main__":
    unittest.main()
