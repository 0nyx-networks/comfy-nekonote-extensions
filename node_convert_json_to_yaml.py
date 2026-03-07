import json
import re

import yaml

from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]

class ConvertJsonToYaml(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="ConvertJsonToYaml",
            display_name="Convert JSON to YAML",
            category="NEKONOTE/Text",
            is_output_node=True,
            inputs=[
                comfy_api_io.String.Input(
                    id="input_string",
                    display_name="JSON String",
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
                    id="multiline_string_enabled",
                    display_name="Multiline String enabled",
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
                    display_name="Output YAML String"
                )
            ]
        )

    @classmethod
    def execute(cls,
                input_string: str = "",
                pretty_enabled: bool = True,
                multiline_string_enabled: bool = True,
                sort_enabled: bool = False,
                **kwargs
                ) -> comfy_api_io.NodeOutput:
        try:
            input_json = json.loads(input_string)
            output_string: str = ""

            # Create a new dumper class for each execution to avoid global state pollution
            dumper_class = type('CustomDumper', (yaml.SafeDumper,), {})

            if multiline_string_enabled:
                dumper_class.add_representer(str, cls._represent_str)

            if pretty_enabled:
                output_string = yaml.dump(input_json, indent=4, allow_unicode=True, sort_keys=sort_enabled, Dumper=dumper_class)
            else:
                output_string = yaml.dump(input_json, allow_unicode=True, sort_keys=sort_enabled, Dumper=dumper_class)

            return comfy_api_io.NodeOutput(output_string)
        except json.JSONDecodeError as ex:
            return comfy_api_io.NodeOutput(json.dumps({"error": f"Invalid JSON: {ex}"}))
        except Exception as ex:
            return comfy_api_io.NodeOutput(json.dumps({"error": f"Invalid JSON: {ex}"}))

    @classmethod
    def _represent_str(cls, dumper, instance):
        if "\n" in instance:
            instance = re.sub(' +\n| +$', '\n', instance)
            return dumper.represent_scalar('tag:yaml.org,2002:str',instance,style='|')
        else:
            return dumper.represent_scalar('tag:yaml.org,2002:str',instance)
