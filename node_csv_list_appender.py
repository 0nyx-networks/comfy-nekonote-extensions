from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]

class CsvListAppender(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="CsvListAppender",
            display_name="CSV List Appender",
            category="NEKONOTE/Text",
            is_output_node=True,
            inputs=[
                comfy_api_io.String.Input(
                    id="input_csv_string",
                    display_name="CSV String",
                    default="",
                    multiline=True,
                    optional=False
                ),
                comfy_api_io.String.Input(
                    id="append_value",
                    display_name="Append value",
                    default="",
                    multiline=True,
                    optional=False
                ),
            ],
            outputs=[
                comfy_api_io.String.Output(
                    id="output_csv_string",
                    display_name="Output CSV String"
                )
            ]
        )

    @classmethod
    def execute(cls,
                input_csv_string: str = "",
                append_value: str = "",
                **kwargs) -> comfy_api_io.NodeOutput:

        if append_value:
            # 既存の値をすべて取得
            existing_lines = set(input_csv_string.strip().split(',')) if input_csv_string.strip() else set()

            # 重複していなければ追加
            if append_value not in existing_lines:
                if input_csv_string and not input_csv_string.endswith(","):
                    input_csv_string += ","
                input_csv_string += append_value

        return comfy_api_io.NodeOutput(input_csv_string)
