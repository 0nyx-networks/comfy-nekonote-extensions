from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]

class CalculateOptimizeResolution(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="CalculateOptimizeResolution",
            display_name="Calculate Optimize Resolution",
            category="NEKONOTE/Utils",
            is_output_node=True,
            inputs=[
                comfy_api_io.Int.Input("input_width",
                    display_name="入力イメージ幅",
                    default=1024,
                    min=0,
                    optional=False,
                    display_mode=comfy_api_io.NumberDisplay.number
                ),
                comfy_api_io.Int.Input("input_height",
                    display_name="入力イメージ高さ",
                    default=1024,
                    min=0,
                    optional=False,
                    display_mode=comfy_api_io.NumberDisplay.number
                ),
                comfy_api_io.Int.Input("desired_width",
                    display_name="希望イメージ幅",
                    default=1024,
                    min=0,
                    step=2,
                    optional=False,
                    display_mode=comfy_api_io.NumberDisplay.number
                ),
                comfy_api_io.Int.Input("desired_height",
                    display_name="希望イメージ高さ",
                    default=1024,
                    min=0,
                    step=2,
                    optional=False,
                    display_mode=comfy_api_io.NumberDisplay.number
                ),
            ],
            outputs=[
                comfy_api_io.Int.Output("width"),
                comfy_api_io.Int.Output("height")
            ]
        )

    @classmethod
    def execute(cls, input_width: int, input_height: int, desired_width: int, desired_height: int, **kwargs) -> None:
        # Calculate optimized resolution
        # アスペクト比を計算
        aspect_ratio = input_width / input_height

        # Option 1: desired_widthに合わせる
        width1 = desired_width
        height1 = round(width1 / aspect_ratio)

        # Option 2: desired_heightに合わせる
        height2 = desired_height
        width2 = round(height2 * aspect_ratio)

        # どちらが要求サイズに近いか判定（マンハッタン距離で判定）
        distance1 = abs(width1 - desired_width) + abs(height1 - desired_height)
        distance2 = abs(width2 - desired_width) + abs(height2 - desired_height)

        calculation_width: int
        calculation_height: int
        if distance1 <= distance2:
            calculation_width = width1
            calculation_height = height1
        else:
            calculation_width = width2
            calculation_height = height2

        return comfy_api_io.NodeOutput(calculation_width, calculation_height)
