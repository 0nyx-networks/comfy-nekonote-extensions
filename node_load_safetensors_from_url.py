import tempfile
from pathlib import Path
from typing import Any, cast
import hashlib

from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]
import folder_paths # pyright: ignore[reportMissingImports]
import httpx
import shutil
import diskcache

from .utils import Utils

class LoadSafetensorsFromUrl(comfy_api_io.ComfyNode):
    # キャッシュのサイズ制限: 2GB
    CACHE_SIZE_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB in bytes

    @classmethod
    def _get_cache_dir(cls, model_type: str) -> Path:
        """モデルタイプ別のキャッシュディレクトリを取得"""
        path_dir: str = folder_paths.folder_names_and_paths[model_type][0][0]
        cache_dir = Path(path_dir) / ".safetensors_url_cache"
        return cache_dir

    @classmethod
    def _get_cache(cls, model_type: str) -> diskcache.Cache:
        """キャッシュディレクトリを初期化してCacheオブジェクトを返す"""
        cache_dir = cls._get_cache_dir(model_type)
        cache_dir.parent.mkdir(parents=True, exist_ok=True)
        cache = diskcache.Cache(str(cache_dir), size_limit=cls.CACHE_SIZE_LIMIT)
        return cache

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
    def execute(cls, safetensors_url: str, model_type: str, **kwargs) -> Any:
        try:
            # 最初のディレクトリを使う場合
            path_dir: str = cast(str, folder_paths.folder_names_and_paths[model_type][0][0])

            # キャッシュを確認
            cache = cls._get_cache(model_type)
            if safetensors_url in cache:
                cached_file_path: str = cast(str, cache[safetensors_url])
                if Path(cached_file_path).exists():
                    print(f"[LoadSafetensorsFromUrl] Using cached file: {cached_file_path}")
                    return comfy_api_io.NodeOutput(Path(cached_file_path).name)
                else:
                    # キャッシュエントリは存在するがファイルが削除されている場合
                    print(f"[LoadSafetensorsFromUrl] Cached file not found, re-downloading: {cached_file_path}")
                    del cache[safetensors_url]

            # URLスキームの確認
            if not (safetensors_url.startswith("http://") or safetensors_url.startswith("https://")):
                print(f"[LoadSafetensorsFromUrl] ERROR: Unsupported URL scheme.")
                return comfy_api_io.NodeOutput("")

            # 一時ファイルを使用してダウンロード
            with tempfile.NamedTemporaryFile(delete=False, suffix=".safetensors") as tmp_file:
                temp_file_path = Path(tmp_file.name)
                try:
                    # ストリーミングダウンロード
                    with httpx.stream("GET", safetensors_url) as response:
                        response.raise_for_status()
                        for chunk in response.iter_bytes(chunk_size=8192):
                            tmp_file.write(chunk)

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

                    # SHA3-512でハッシュ値を計算してファイル名として使用
                    sha3_hash = hashlib.sha3_512(file_data).hexdigest()
                    file_size = len(file_data)
                    print(f"[LoadSafetensorsFromUrl] Downloaded file size: {file_size} bytes, SHA3-512: {sha3_hash}")
                    file_name = f"download_{sha3_hash}_{file_size}.safetensors"
                    save_path_obj = Path(path_dir, file_name)

                    if save_path_obj.exists():
                        print(f"[LoadSafetensorsFromUrl] File already exists at: {save_path_obj}")
                        # キャッシュに保存
                        cache[safetensors_url] = str(save_path_obj)
                        return comfy_api_io.NodeOutput(save_path_obj.name)

                    save_path_obj.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(temp_file_path), str(save_path_obj))

                    # ダウンロード完了後、キャッシュに保存
                    cache[safetensors_url] = str(save_path_obj)

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
