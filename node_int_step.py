from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]

class PrimitiveIntStep(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        base_size : int = 256

        return comfy_api_io.Schema(
            node_id="PrimitiveIntStep",
            display_name="Primitive Int Step",
            category="NEKONOTE/Utils",
            is_output_node=True,
            inputs=[
                comfy_api_io.Int.Input("choice",
                    default=base_size,
                    min=base_size,
                    step=base_size,
                    max=base_size * 32,
                    optional=False,
                    display_mode=comfy_api_io.NumberDisplay.number
                ),
            ],
            outputs=[
                comfy_api_io.Int.Output("value"),
            ]
        )

    @classmethod
    def execute(cls, choice: int, **kwargs) -> None:
        return comfy_api_io.NodeOutput(choice)
