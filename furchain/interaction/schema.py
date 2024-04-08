from concurrent.futures import ThreadPoolExecutor, Future
from typing import Iterator, Callable

from langchain_core.output_parsers import BaseTransformOutputParser

from furchain.interaction.actions import Action


class Interaction:
    def __init__(self, action: Action, future: Future, executor: Callable):
        self.action = action
        self.future = future
        self.executor = executor

    def execute(self):
        return self.executor(self.future.result())


class InteractionParser:

    def __init__(self, validator: Callable, executor: Callable, evaluator: Callable, num_workers: int = 1):
        self.validator = validator
        self.execution_pool = ThreadPoolExecutor(max_workers=num_workers)
        self.executor = executor
        self.evaluator = evaluator

    def match(self, action: Action) -> bool:
        return self.validator(action)

    def parse(self, action: Action) -> Interaction:
        print(f"Submit: {action}")
        return Interaction(action, self.execution_pool.submit(self.executor, action.action_parameter), self.evaluator)


class InteractionOutputParser(BaseTransformOutputParser):
    parsers: list[InteractionParser]

    class Config:
        arbitrary_types_allowed = True

    def parse(self, action: Action) -> Action:
        return action

    def _transform(self, input: Iterator[Action]) -> Iterator[Interaction]:
        for action in input:
            for parser in self.parsers:
                if parser.match(action):
                    yield parser.parse(action)
                    break
            else:
                print(f"No parser found for action: {action}")
