from comfy_api.latest import ComfyExtension, io as comfy_api_io # pyright: ignore[reportMissingImports]

class ComfyNekonoteExtensions(ComfyExtension):
    async def get_node_list(self) -> list[type[comfy_api_io.ComfyNode]]:
        from .node_calculate_optimize_resolution import CalculateOptimizeResolution
        from .node_primitive_combo_list import PrimitiveComboList
        from .node_primitive_int_step import PrimitiveIntStep
        return [
                    CalculateOptimizeResolution,
                    PrimitiveComboList,
                    PrimitiveIntStep,
               ]

async def comfy_entrypoint() -> ComfyExtension:
    return ComfyNekonoteExtensions()
