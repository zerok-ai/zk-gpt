from typing import List, Dict, Optional, Any
from typing import Any, Dict, List, Optional

from langchain.callbacks.manager import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.chains.base import Chain
from langchain.pydantic_v1 import Extra, root_validator
from langchain.utils.input import get_color_mapping


class CustomSimpleSequentialChain(Chain):
    """Simple chain where the outputs of one step feed directly into the next."""

    chains: List[Chain]
    strip_outputs: bool = False
    input_key: str = "input"  #: :meta private:
    output_key: str = "output"  #: :meta private:
    custom_data: List[Dict[str, Any]]  # Custom data for each chain

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Expect input key.

        :meta private:
        """
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        """Return output key.

        :meta private:
        """
        return [self.output_key]

    @root_validator()
    def validate_chains(cls, values: Dict) -> Dict:
        """Validate that chains are all single input/output."""
        for chain in values["chains"]:
            if len(chain.input_keys) != 1:
                raise ValueError(
                    "Chains used in SimplePipeline should all have one input, got "
                    f"{chain} with {len(chain.input_keys)} inputs."
                )
            if len(chain.output_keys) != 1:
                raise ValueError(
                    "Chains used in SimplePipeline should all have one output, got "
                    f"{chain} with {len(chain.output_keys)} outputs."
                )
        return values

    def _call(
        self,
        inputs: Dict[str, Any],  # Updated to accept Any
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:  # Updated to return Any
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        _input = inputs[self.input_key]
        color_mapping = get_color_mapping([str(i) for i in range(len(self.chains))])
        for i, chain in enumerate(self.chains):
            chain_inputs = {"input": _input, "custom_data": self.custom_data[i]}  # Pass custom data to each chain
            _output = chain.run(chain_inputs, callbacks=_run_manager.get_child(f"step_{i+1}"))
            if self.strip_outputs:
                _output = _output.strip()
            _run_manager.on_text(
                _output, color=color_mapping[str(i)], end="\n", verbose=self.verbose
            )
            _input = _output  # Update the input for the next chain
        return {self.output_key: _output}

    async def _acall(
        self,
        inputs: Dict[str, Any],  # Updated to accept Any
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:  # Updated to return Any
        _run_manager = run_manager or AsyncCallbackManagerForChainRun.get_noop_manager()
        _input = inputs[self.input_key]
        color_mapping = get_color_mapping([str(i) for i in range(len(self.chains))])
        for i, chain in enumerate(self.chains):
            chain_inputs = {"input": _input, "custom_data": self.custom_data[i]}  # Pass custom data to each chain
            _output = await chain.arun(
                chain_inputs, callbacks=_run_manager.get_child(f"step_{i+1}")
            )
            if self.strip_outputs:
                _output = _output.strip()
            await _run_manager.on_text(
                _output, color=color_mapping[str(i)], end="\n", verbose=self.verbose
            )
            _input = _output  # Update the input for the next chain
        return {self.output_key: _output}
