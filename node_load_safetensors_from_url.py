import tempfile
from pathlib import Path
from typing import Any

from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]
import folder_paths # pyright: ignore[reportMissingImports]
import httpx
import shutil

from .utils import Utils

class LoadSafetensorsFromUrl(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="LoadSafetensorsFromUrl",
            display_name="Load Safetensors from URL",
            category="NEKONOTE/Load",
            is_output_node=False,
            inputs=[
                comfy_api_io.String.Input("safetensors_url",
                    default="",
                    multiline=False,
                    optional=False
                ),
                comfy_api_io.String.Input("file_name",
                    default="",
                    multiline=False,
                    optional=False
                ),
                comfy_api_io.Combo.Input("model_type",
                    display_name="Type",
                    options=[
                        "checkpoints",
                        "clip_vision",
                        "controlnet",
                        "diffustion_models",
                        "loras",
                        "text_encoders",
                    ],
                    optional=False,
                ),
            ],
            outputs=[
                comfy_api_io.String.Output("file_name"),
            ]
        )

    @classmethod
    def execute(cls, safetensors_url: str, file_name: str, model_type: str, **kwargs) -> Any:
        try:
            # 最初のディレクトリを使う場合
            path_dir: str = folder_paths.folder_names_and_paths[model_type][0][0]

            # 最終パスを構築
            save_path_obj = Path(path_dir, file_name)

            if save_path_obj.exists():
                print(f"[LoadSafetensorsFromUrl] File already exists at: {save_path_obj}")
                return comfy_api_io.NodeOutput(save_path_obj.name)

            # 一時ファイルを使用してダウンロード
            with tempfile.NamedTemporaryFile(delete=False, suffix=".safetensors") as tmp_file:
                temp_file_path = Path(tmp_file.name)
                try:
                    # URLからSafetensorsファイルを取得
                    if safetensors_url.startswith("http://") or safetensors_url.startswith("https://"):
                        # ストリーミングダウンロード
                        with httpx.stream("GET", safetensors_url) as response:
                            response.raise_for_status()
                            for chunk in response.iter_bytes(chunk_size=8192):
                                tmp_file.write(chunk)

                    else:
                        print(f"[LoadSafetensorsFromUrl] ERROR: Unsupported URL scheme.")
                        return comfy_api_io.NodeOutput("")

                    tmp_file.flush()

                    # 一時ファイルからバリデーション
                    with open(temp_file_path, "rb") as f:
                        file_data = f.read()

                    if not file_data:
                        print(f"[LoadSafetensorsFromUrl] ERROR: No file data retrieved.")
                        return comfy_api_io.NodeOutput("")

                    if not Utils._validate_safetensors_data(file_data):
                        print(f"[LoadSafetensorsFromUrl] ERROR: Invalid safetensors format.")
                        return comfy_api_io.NodeOutput("")

                    save_path_obj.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(temp_file_path), str(save_path_obj))

                    print(f"[LoadSafetensorsFromUrl] Successfully saved safetensors file to: {save_path_obj}")
                    return comfy_api_io.NodeOutput(save_path_obj.name)

                finally:
                    # 一時ファイルがまだ存在する場合は削除
                    if temp_file_path.exists():
                        temp_file_path.unlink()

        except Exception as ex:
            print(f"[LoadSafetensorsFromUrl] ERROR: {ex}")
            import traceback
            traceback.print_exc()

        return comfy_api_io.NodeOutput("")
