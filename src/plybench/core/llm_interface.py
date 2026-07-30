from __future__ import annotations

from plybench.common.enums import PlayerOrder


class LLMAction:
    def __init__(self, string: str) -> None:
        self.string = string

    def to_prompt(self) -> str:
        return self.string

    def __str__(self) -> str:
        return f"LLMAction: {self.string}"

    def __repr__(self) -> str:
        return self.__str__()


class LLMPosition:
    def __init__(self, string: str) -> None:
        self.string = string

    def to_prompt(self) -> str:
        return self.string

    def __str__(self) -> str:
        return f"LLMPosition: {self.string}"

    def __repr__(self) -> str:
        return self.__str__()


class LLMPartialState:
    def __init__(self, string: str) -> None:
        self.string = string

    def to_prompt(self) -> str:
        return self.string

    def __str__(self) -> str:
        return f"LLMPartialState: {self.string}"

    def __repr__(self) -> str:
        return self.__str__()


class LLMObservation:
    @staticmethod
    def actions_prompt(actions: list[LLMAction]) -> str:
        return ", ".join(action.to_prompt() for action in actions)

    @staticmethod
    def positions_prompt(positions: list[LLMPosition]) -> str:
        return ", ".join(position.to_prompt() for position in positions)

    @staticmethod
    def partial_states_prompt(partial_states: list[LLMPartialState]) -> str:
        return ", ".join(partial_state.to_prompt() for partial_state in partial_states)

    def __init__(
        self,
        state: str,
        partial_states: list[LLMPartialState],
        i_actions: list[LLMAction],
        o_actions: list[LLMAction],
        i_positions: list[LLMPosition],
        o_positions: list[LLMPosition],
        player_order: PlayerOrder,
    ) -> None:
        # canonical open spiel observation, typically a grid
        self.state = state
        # state represented as partials, i.e. rows, columns, piles etc.
        self.partial_states = partial_states
        # the actions of both players
        self.i_actions = i_actions
        self.o_actions = o_actions
        # the positions held by both players
        self.i_positions = i_positions
        self.o_positions = o_positions
        # the order of the current player
        self.player_order = player_order

    def all_partial_states_prompt(self) -> str:
        return LLMObservation.partial_states_prompt(self.partial_states)

    def i_actions_prompt(self) -> str:
        return LLMObservation.actions_prompt(self.i_actions)

    def i_positions_prompt(self) -> str:
        return LLMObservation.positions_prompt(self.i_positions)

    def o_actions_prompt(self) -> str:
        return LLMObservation.actions_prompt(self.o_actions)

    def o_positions_prompt(self) -> str:
        return LLMObservation.positions_prompt(self.o_positions)

    def __str__(self) -> str:
        return (
            f"LLMObservation:\n{self.state}\n"
            f"Partial States: {self.all_partial_states_prompt()}\n"
            f"Positions[i]: {self.i_positions_prompt()}\nActions[i]: {self.i_actions_prompt()}\n"
            f"Positions[o]: {self.o_positions_prompt()}\nActions[o]: {self.o_actions_prompt()}"
        )

    def __repr__(self) -> str:
        return self.__str__()
