from typing import Any

from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]
import comfy.sd # pyright: ignore[reportMissingImports]
import comfy.utils # pyright: ignore[reportMissingImports]
import folder_paths # pyright: ignore[reportMissingImports]

class LoadLoraFromFile(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="LoadLoRAFromFile",
            display_name="Load LoRA from File",
            category="NEKONOTE/Load",
            is_output_node=False,
            inputs=[
                comfy_api_io.Model.Input("model"),
                comfy_api_io.Clip.Input("clip"),
                comfy_api_io.String.Input(
                    "file_name",
                    force_input=True,   # ← ワイヤー接続を強制（ドロップダウンなし）
                ),
                comfy_api_io.Float.Input("strength_model",
                    default=1.0,
                    min=-100.0,
                    max=100.0,
                    step=0.01,
                ),
                comfy_api_io.Float.Input("strength_clip",
                    default=1.0,
                    min=-100.0,
                    max=100.0,
                    step=0.01,
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
        file_name: str,
        strength_model: float,
        strength_clip: float,
        raise_error_on_failure: bool = False,
        **kwargs
    ) -> Any:
        if not file_name:
            print("[LoadLoraFromFile] ERROR: file_name is empty.")
            if raise_error_on_failure:
                raise ValueError("file_name is empty.")
            return comfy_api_io.NodeOutput(model, clip)

        # folder_pathsからフルパスを解決
        lora_path = folder_paths.get_full_path("loras", file_name)

        if lora_path is None:
            print(f"[LoadLoraFromFile] ERROR: LoRA not found: {file_name}")
            if raise_error_on_failure:
                raise FileNotFoundError(f"LoRA not found: {file_name}")
            return comfy_api_io.NodeOutput(model, clip)

        try:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            model_patched, clip_patched = comfy.sd.load_lora_for_models(
                model, clip, lora, strength_model, strength_clip
            )
            print(f"[LoadLoraFromFile] Successfully loaded LoRA: {file_name}")
            return comfy_api_io.NodeOutput(model_patched, clip_patched)

        except Exception as ex:
            print(f"[LoadLoraFromFile] ERROR: {ex}")
            import traceback
            traceback.print_exc()
            if raise_error_on_failure:
                raise ex
            return comfy_api_io.NodeOutput(model, clip)
