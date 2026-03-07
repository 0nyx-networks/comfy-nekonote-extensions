import json

from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]

class JsonValueMutator(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="JsonValueMutator",
            display_name="JSON Value Mutator",
            category="NEKONOTE/Text",
            is_output_node=True,
            inputs=[
                comfy_api_io.String.Input(
                    id="input_json_string",
                    display_name="JSON String",
                    default="",
                    multiline=True,
                    optional=False
                ),
                comfy_api_io.String.Input(
                    id="append_key",
                    display_name="Append key",
                    default="",
                    multiline=False,
                    optional=False
                ),
                comfy_api_io.String.Input(
                    id="append_value",
                    display_name="Append value",
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
                    id="output_json_string",
                    display_name="Output JSON String"
                )
            ]
        )

    @classmethod
    def execute(cls,
                input_json_string: str = "",
                append_key: str = "",
                append_value: str = "",
                pretty_enabled: bool = True,
                sort_enabled: bool = False,
                **kwargs) -> comfy_api_io.NodeOutput:
        try:
            input_json = json.loads(input_json_string)
        except json.JSONDecodeError as ex:
            print(f"[JsonValueMutator] ERROR: Invalid JSON: {ex}")
            return comfy_api_io.NodeOutput(json.dumps({"error": f"Invalid JSON: {ex}"}))

        # Perform JSON manipulation or processing here
        if append_key:
            try:
                input_json[append_key] = json.loads(append_value)
            except json.JSONDecodeError as ex:
                print(f"[JsonValueMutator] WARNING: Invalid JSON for value: {ex}")
                input_json[append_key] = append_value

        output_string: str = ""
        if pretty_enabled:
            output_string = json.dumps(input_json, indent=4, ensure_ascii=False, sort_keys=sort_enabled)
        else:
            output_string = json.dumps(input_json, ensure_ascii=False, sort_keys=sort_enabled)

        return comfy_api_io.NodeOutput(output_string)
