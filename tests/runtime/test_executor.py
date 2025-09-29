from bambusa.runtime.executor import Executor


def test_mul_initialises_missing_register_to_operand() -> None:
    executor = Executor([
        {
            "op": "mul",
            "target": "result",
            "value": 7,
        }
    ])

    executor.run()

    assert executor.state["result"] == 7
