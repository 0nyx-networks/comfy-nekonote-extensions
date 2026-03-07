from io import StringIO
import csv
import json
import re
import yaml

from comfy_api.latest import io as comfy_api_io, ui as comfy_api_ui # pyright: ignore[reportMissingImports]


class DisplayStringData(comfy_api_io.ComfyNode):

    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="DisplayStringData",
            display_name="Display String Data",
            category="NEKONOTE/Text",
            is_output_node=True,
            inputs=[
                comfy_api_io.String.Input(
                    id="input_string",
                    display_name="Input string",
                ),
                comfy_api_io.Boolean.Input(
                    id="display_pretty_enabled",
                    display_name="Display Pretty enabled",
                    default=True,
                ),
                comfy_api_io.Combo.Input(
                    id="string_format_determination",
                    display_name="String format determination",
                    default="AUTO_DETECT",
                    options=["AUTO_DETECT", "JSON", "YAML", "CSV"],
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
                    display_name="Output String"
                )
            ],
        )

    @classmethod
    def _pretty_json(cls, text, sort_enabled: bool):
        parsed = json.loads(text)
        return json.dumps(parsed, indent=4, ensure_ascii=False, sort_keys=sort_enabled)

    @classmethod
    def _pretty_yaml(cls, text, sort_enabled: bool, multiline_string_enabled: bool =True):
        parsed = yaml.safe_load(text)
        if parsed is None:
            return ""

        # Create a new dumper class for each execution to avoid global state pollution
        dumper_class = type('CustomDumper', (yaml.SafeDumper,), {})

        if multiline_string_enabled:
            dumper_class.add_representer(str, cls._represent_str)

        return yaml.dump(parsed, indent=4, allow_unicode=True, sort_keys=sort_enabled, Dumper=dumper_class)

    @classmethod
    def _pretty_csv(cls, text):
        f = StringIO(text)
        reader = csv.reader(f)
        return "\n".join([", ".join(row) for row in reader])

    @classmethod
    def _yaml_represent_str(cls, dumper, instance):
        if "\n" in instance:
            instance = re.sub(' +\n| +$', '\n', instance)
            return dumper.represent_scalar('tag:yaml.org,2002:str',instance,style='|')
        else:
            return dumper.represent_scalar('tag:yaml.org,2002:str',instance)

    @classmethod
    def execute(cls,
                input_string: str,
                display_pretty_enabled: bool,
                string_format_determination: str,
                sort_enabled: bool,
                **kwargs
                ) -> comfy_api_io.NodeOutput:

        if display_pretty_enabled:

            if string_format_determination in ("JSON", "AUTO_DETECT"):
                try:
                    pretty_string = cls._pretty_json(input_string, sort_enabled)
                    return comfy_api_io.NodeOutput(
                        pretty_string,
                        ui=comfy_api_ui.PreviewText(pretty_string)
                    )
                except Exception:
                    pass

            if string_format_determination in ("YAML", "AUTO_DETECT"):
                try:
                    pretty_string = cls._pretty_yaml(input_string, sort_enabled)
                    return comfy_api_io.NodeOutput(
                        pretty_string,
                        ui=comfy_api_ui.PreviewText(pretty_string)
                    )
                except Exception:
                    pass

            if string_format_determination in ("CSV", "AUTO_DETECT"):
                try:
                    pretty_string = cls._pretty_csv(input_string)
                    return comfy_api_io.NodeOutput(
                        pretty_string,
                        ui=comfy_api_ui.PreviewText(pretty_string)
                    )
                except Exception:
                    pass

        return comfy_api_io.NodeOutput(
            input_string,
            ui=comfy_api_ui.PreviewText(input_string)
        )
