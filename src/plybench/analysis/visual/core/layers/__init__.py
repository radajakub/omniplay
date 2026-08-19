"""Chart types. Each is a dataclass satisfying the Layer protocol; adding one changes nothing else."""

from plybench.analysis.visual.core.layers.base import DrawContext, Layer
from plybench.analysis.visual.core.layers.baseline import BaselineLayer
from plybench.analysis.visual.core.layers.line import LineLayer

__all__ = ["BaselineLayer", "DrawContext", "Layer", "LineLayer"]
