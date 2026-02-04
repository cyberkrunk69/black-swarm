import unittest
from consensus_node import ConsensusNode


def model_one(x):
    return x % 2  # 0 or 1


def model_two(x):
    return 1 if x > 5 else 0


def model_three(x):
    return 0  # always 0


class TestConsensusNode(unittest.TestCase):
    def test_majority_vote(self):
        cn = ConsensusNode(strategy="majority")
        cn.register_model("m1", model_one)
        cn.register_model("m2", model_two)
        cn.register_model("m3", model_three)

        # For x=7: model_one=1, model_two=1, model_three=0 => majority 1
        self.assertEqual(cn.consensus(7), 1)

        # For x=2: model_one=0, model_two=0, model_three=0 => majority 0
        self.assertEqual(cn.consensus(2), 0)

    def test_average_strategy(self):
        cn = ConsensusNode(strategy="average")
        cn.register_model("m1", lambda x: x * 1.0)
        cn.register_model("m2", lambda x: x + 10)
        cn.register_model("m3", lambda x: 5)

        # (7 + 17 + 5) / 3 = 9.666...
        self.assertAlmostEqual(cn.consensus(7), (7 + 17 + 5) / 3)

    def test_no_models(self):
        cn = ConsensusNode()
        with self.assertRaises(RuntimeError):
            cn.consensus(1)


if __name__ == "__main__":
    unittest.main()