from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from omniplay.common.enums import PlayerOrder
from omniplay.core.game import OpenSpielAction, OpenSpielObservation
from omniplay.core.llm_interface import LLMAction, LLMObservation, LLMPartialState, LLMPosition


class InterfaceTransformer(ABC):
    @abstractmethod
    def _inner_llm_action(self, action: InterfaceAction) -> str:
        raise NotImplementedError

    def llm_action(self, action: InterfaceAction) -> LLMAction:
        inner_llm_action = self._inner_llm_action(action)
        return LLMAction(f'<{inner_llm_action}>')

    @abstractmethod
    def display_action(self, action: InterfaceAction) -> str:
        raise NotImplementedError

    @abstractmethod
    def _inner_llm_state(self, observation: InterfaceObservation) -> str:
        raise NotImplementedError

    @abstractmethod
    def _inner_llm_partial_states(self, observation: InterfaceObservation) -> list[str]:
        raise NotImplementedError

    def llm_partial_states(self, observation: InterfaceObservation) -> list[LLMPartialState]:
        return [LLMPartialState(partial_state) for partial_state in self._inner_llm_partial_states(observation)]

    @abstractmethod
    def _inner_llm_positions(self, observation: InterfaceObservation) -> tuple[list[str], list[str]]:
        raise NotImplementedError

    def llm_positions(self, observation: InterfaceObservation) -> tuple[list[LLMPosition], list[LLMPosition]]:
        i_positions, o_positions = self._inner_llm_positions(observation)
        return [LLMPosition(pos) for pos in i_positions], [LLMPosition(pos) for pos in o_positions]

    def llm_observation(self, observation: InterfaceObservation) -> LLMObservation:
        state = self._inner_llm_state(observation)
        partial_states = self.llm_partial_states(observation)
        i_actions = [self.llm_action(action) for action in observation.i_actions]
        o_actions = [self.llm_action(action) for action in observation.o_actions]
        i_positions, o_positions = self.llm_positions(observation)
        return LLMObservation(state, partial_states, i_actions, o_actions, i_positions, o_positions, observation.player_order)

    @abstractmethod
    def _inner_display_state(self, observation: InterfaceObservation) -> str:
        raise NotImplementedError

    def display_observation(self, observation: InterfaceObservation) -> str:
        state = self._inner_display_state(observation)
        i_actions = ', '.join(f'{action}' for action in observation.i_actions)
        o_actions = ', '.join(f'{action}' for action in observation.o_actions)
        return f'State:\n{state}\nI: {i_actions}\nO: {o_actions}'

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_other_params(self) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def set_state(self) -> None:
        raise NotImplementedError


class InterfaceAction(ABC):
    @staticmethod
    @abstractmethod
    def from_openspiel(action: OpenSpielAction, game_transformer: InterfaceTransformer) -> InterfaceAction:
        raise NotImplementedError

    def __init__(self, number: int, interface_transformer: InterfaceTransformer) -> None:
        self.number = number
        self.interface_transformer = interface_transformer

    @abstractmethod
    def to_openspiel(self) -> OpenSpielAction:
        raise NotImplementedError

    def to_llm(self) -> LLMAction:
        return self.interface_transformer.llm_action(self)

    def __str__(self) -> str:
        return self.interface_transformer.display_action(self)

    def __repr__(self) -> str:
        return self.__str__()


class InterfaceObservation(ABC):
    @staticmethod
    @abstractmethod
    def from_openspiel(observation: OpenSpielObservation, interface_transformer: InterfaceTransformer) -> InterfaceObservation:
        raise NotImplementedError

    def __init__(self, os_observation: OpenSpielObservation, i_actions: list[InterfaceAction], o_actions: list[InterfaceAction], interface_transformer: InterfaceTransformer) -> None:
        # keep the original observation for the MCTS/optimal players to use
        self.os_observation = os_observation
        self.i_actions = i_actions
        self.o_actions = o_actions
        self.player_order = PlayerOrder.from_int(os_observation.player)
        self.interface_transformer = interface_transformer

    def to_llm(self) -> LLMObservation:
        return self.interface_transformer.llm_observation(self)

    def __str__(self) -> str:
        return self.interface_transformer.display_observation(self)

    def __repr__(self) -> str:
        return self.__str__()
