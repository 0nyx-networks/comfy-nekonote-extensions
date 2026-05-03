import json
from typing import Any

from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]
import comfy.sd # pyright: ignore[reportMissingImports]
import comfy.utils # pyright: ignore[reportMissingImports]
import folder_paths # pyright: ignore[reportMissingImports]

class LoadLoraFromMultipleFiles(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="LoadLoRAFromMultipleFiles",
            display_name="Load LoRA from Multiple Files",
            category="NEKONOTE/Load",
            is_output_node=False,
            inputs=[
                comfy_api_io.Model.Input("model"),
                comfy_api_io.Clip.Input("clip"),
                comfy_api_io.String.Input(
                    "lora_params_json",
                    multiline=True,
                    default='[]',
                    optional=False,
                    force_input=True,   # ← ワイヤー接続を強制（ドロップダウンなし）
                ),
                comfy_api_io.Boolean.Input(
                    id="raise_error_on_failure",
                    display_name="Raise Error on Failure",
                    default=False,
                    optional=True,
                ),
            ],
            outputs=[
                comfy_api_io.Model.Output("model"),
                comfy_api_io.Clip.Output("clip"),
            ]
        )

    @classmethod
    def execute(
        cls,
        model: Any,
        clip: Any,
        lora_params_json: str,
        raise_error_on_failure: bool = False,
        **kwargs
    ) -> Any:
        if not lora_params_json:
            print("[LoadLoraFromMultipleFiles] ERROR: lora_params_json is empty.")
            if raise_error_on_failure:
                raise ValueError("lora_params_json is empty.")
            return comfy_api_io.NodeOutput(model, clip)

        try:
            lora_params = json.loads(lora_params_json)
        except json.JSONDecodeError as ex:
            print(f"[LoadLoraFromMultipleFiles] ERROR: Failed to parse lora_params_json: {ex}")
            if raise_error_on_failure:
                raise ex
            return comfy_api_io.NodeOutput(model, clip)

        if not lora_params:
            print("[LoadLoraFromMultipleFiles] ERROR: lora_params list is empty.")
            return comfy_api_io.NodeOutput(model, clip)

        model_patched, clip_patched = model, clip
        for entry in lora_params:
            if not isinstance(entry, dict):
                print(f"[LoadLoraFromMultipleFiles] ERROR: Each item in lora_params should be a dict. Skipping invalid item: {entry}")
                if raise_error_on_failure:
                    raise ValueError(f"Each item in lora_params should be a dict. Invalid item: {entry}")
                continue

            if any(key not in entry for key in ["file_name","strength_model", "strength_clip"]):
                print(f"[LoadLoraFromMultipleFiles] ERROR: Each lora_param dict must contain 'file_name', 'strength_model', and 'strength_clip' keys. Skipping invalid item: {entry}")
                if raise_error_on_failure:
                    raise ValueError(f"Each lora_param dict must contain 'file_name', 'strength_model', and 'strength_clip' keys. Invalid item: {entry}")
                continue

            file_name = entry.get("file_name")
            strength_model = entry.get("strength_model", 1.0)
            strength_clip = entry.get("strength_clip", 1.0)
            try:
                strength_model = float(strength_model)
                strength_clip = float(strength_clip)
            except (TypeError, ValueError) as ex:
                print(f"[LoadLoraFromMultipleFiles] ERROR: 'strength_model' and 'strength_clip' must be convertible to float. Skipping invalid item: {entry}. Error: {ex}")
                if raise_error_on_failure:
                    raise ValueError(f"'strength_model' and 'strength_clip' must be convertible to float. Invalid item: {entry}. Error: {ex}")
                continue

            if not file_name:
                print("[LoadLoraFromMultipleFiles] ERROR: LoRA file_name is missing in lora_params.")
                if raise_error_on_failure:
                    raise ValueError("LoRA file_name is missing in lora_params.")
                continue

            # folder_pathsからフルパスを解決
            lora_path = folder_paths.get_full_path("loras", file_name)

            if lora_path is None:
                print(f"[LoadLoraFromMultipleFiles] ERROR: LoRA not found: {file_name}")
                if raise_error_on_failure:
                    raise FileNotFoundError(f"LoRA not found: {file_name}")
                continue

            try:
                lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
                model_patched, clip_patched = comfy.sd.load_lora_for_models(
                    model_patched, clip_patched, lora, strength_model, strength_clip
                )
                print(f"[LoadLoraFromMultipleFiles] Successfully loaded LoRA: {file_name}")

            except Exception as ex:
                print(f"[LoadLoraFromMultipleFiles] ERROR: {ex}")
                if raise_error_on_failure:
                    raise ex
                continue

        return comfy_api_io.NodeOutput(model_patched, clip_patched)
