import csv
import json

from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]

class ConvertCsvToJson(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="ConvertCsvToJson",
            display_name="Convert CSV to JSON",
            category="NEKONOTE/Text",
            is_output_node=True,
            inputs=[
                comfy_api_io.String.Input(
                    id="input_string",
                    display_name="CSV String",
                    default="",
                    multiline=True,
                    optional=False
                ),
                comfy_api_io.Boolean.Input(
                    id="pretty_enabled",
                    display_name="Pretty enabled",
                    default=True,
                ),
                comfy_api_io.Boolean.Input(
                    id="sort_enabled",
                    display_name="Sort keys enabled",
                    default=False,
                ),
            ],
            outputs=[
                comfy_api_io.String.Output(
                    id="output_string",
                    display_name="Output JSON String"
                )
            ]
        )

    @classmethod
    def execute(cls,
                input_string: str = "",
                pretty_enabled: bool = True,
                sort_enabled: bool = False,
                **kwargs
                ) -> comfy_api_io.NodeOutput:
        try:
            input_csv = list(csv.reader(input_string.splitlines()))

            output_string: str = ""
            if pretty_enabled:
                output_string = json.dumps(input_csv, indent=4, ensure_ascii=False, sort_keys=sort_enabled)
            else:
                output_string = json.dumps(input_csv, ensure_ascii=False, sort_keys=sort_enabled)
            return comfy_api_io.NodeOutput(output_string)
        except Exception as ex:
            return comfy_api_io.NodeOutput(json.dumps({"error": f"Invalid CSV: {ex}"}))
