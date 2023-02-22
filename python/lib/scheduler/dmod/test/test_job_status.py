import unittest
from ..scheduler.job.job import JobExecPhase, JobExecStep, JobStatus


class TestJobStatus(unittest.TestCase):

    def setUp(self) -> None:
        self.status_examples = []
        self.name_str_examples = []

        status = JobStatus(phase=JobExecPhase.MODEL_EXEC, step=JobExecStep.AWAITING_ALLOCATION)
        self.status_examples.append(status)
        self.name_str_examples.append(status.name)

        self.status_examples.append(status)
        self.name_str_examples.append("model_exec:awaiting_allocation")

    def tearDown(self) -> None:
        pass

    def test_get_for_name_0_a(self):
        """
        Simple test for example 0.
        """
        example_idx = 0

        expected_status = self.status_examples[example_idx]
        name_str = self.name_str_examples[example_idx]

        parsed_status = JobStatus.get_for_name(name_str)
        self.assertEqual(parsed_status, expected_status)

    def test_get_for_name_0_b(self):
        """
        Test for example 0, but with the name string converted to lowercase.
        """
        example_idx = 0

        expected_status = self.status_examples[example_idx]
        name_str = self.name_str_examples[example_idx].lower()

        parsed_status = JobStatus.get_for_name(name_str)
        self.assertEqual(parsed_status, expected_status)

    def test_get_for_name_1_a(self):
        """
        Simple test for example 1 (which was explicitly set with a lowercase name string).
        """
        example_idx = 0

        expected_status = self.status_examples[example_idx]
        name_str = self.name_str_examples[example_idx]

        parsed_status = JobStatus.get_for_name(name_str)
        self.assertEqual(parsed_status, expected_status)




