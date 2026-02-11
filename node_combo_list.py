from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]

class PrimitiveComboList(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        base_size : int = 256
        size_options : list[int] = [base_size * ratio for ratio in range(1, (32+1))]

        return comfy_api_io.Schema(
            node_id="PrimitiveComboList",
            display_name="Primitive Combo List",
            category="NEKONOTE/Utils",
            is_output_node=True,
            inputs=[
                comfy_api_io.Combo.Input("choice",
                    options=sorted(size_options),
                    optional=False,
                ),
            ],
            outputs=[
                comfy_api_io.Int.Output("value"),
            ]
        )

    @classmethod
    def execute(cls, choice: int, **kwargs) -> None:
        return comfy_api_io.NodeOutput(choice)
