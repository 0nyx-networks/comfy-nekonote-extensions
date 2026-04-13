import json
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

class LoadSafetensorsFromMultipleUrls(comfy_api_io.ComfyNode):
    # キャッシュのサイズ制限: 10GB
    CACHE_SIZE_LIMIT = 10 * 1024 * 1024 * 1024  # 10GB in bytes

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
            node_id="LoadSafetensorsFromMultipleUrls",
            display_name="Load Safetensors from Multiple URLs",
            category="NEKONOTE/Load",
            is_output_node=False,
            inputs=[
                comfy_api_io.String.Input("entries_json",
                    display_name="URLs (JSON list[dict])",
                    default='[{"name": "", "strength_model": 1.0, "strength_clip": 1.0}]',
                    multiline=True,
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
                comfy_api_io.String.Output("results_json"),
            ]
        )

    @classmethod
    def execute(cls, entries_json: str, model_type: str, **kwargs) -> Any:
        # JSONリストをパース
        try:
            urls_list = json.loads(entries_json)
            if not isinstance(urls_list, list):
                urls_list = [urls_list]
        except json.JSONDecodeError:
            print(f"[LoadSafetensorsFromMultipleUrls] ERROR: Invalid JSON format.")
            return comfy_api_io.NodeOutput(json.dumps([]))

        if not urls_list:
            print(f"[LoadSafetensorsFromMultipleUrls] ERROR: URLs list is empty.")
            return comfy_api_io.NodeOutput(json.dumps([]))

        # 最初のディレクトリを使う場合
        path_dir: str = cast(str, folder_paths.folder_names_and_paths[model_type][0][0])
        cache = cls._get_cache(model_type)

        results: list[dict[str, str|float]] = []

        for idx, entry in enumerate(urls_list):
            # 入力形式のバリデーション
            if isinstance(entry, str):
                # 後方互換性: 文字列の場合
                entry = {
                    "name": entry,
                    "strength_model": 1.0,
                    "strength_clip": 1.0
                }
            elif isinstance(entry, dict):
                # 必須フィールドのチェック
                required_fields = ["name", "strength_model", "strength_clip"]
                missing_fields = [field for field in required_fields if field not in entry]
                if missing_fields:
                    print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] WARNING: Missing fields {missing_fields}. Skipping.")
                    continue
            else:
                print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] WARNING: Invalid entry format. Skipping.")
                continue

            safetensors_url: str = str(entry.get("name", "")).strip()
            try:
                strength_model: float = float(entry.get("strength_model", 1.0))
                strength_clip: float = float(entry.get("strength_clip", 1.0))
            except (ValueError, TypeError):
                print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] WARNING: Invalid strength values. Using defaults (1.0).")
                strength_model = 1.0
                strength_clip = 1.0

            if not safetensors_url:
                print(f"[LoadSafetensorsFromMultipleUrls] WARNING: URL at index {idx} is empty. Skipping.")
                continue

            # URLスキームの確認
            if not (safetensors_url.startswith("http://") or safetensors_url.startswith("https://")):
                print(f"[LoadSafetensorsFromMultipleUrls] ERROR: Unsupported URL scheme at index {idx}: {safetensors_url}")
                continue

            # キャッシュを確認
            if safetensors_url in cache:
                cached_file_path: str = cast(str, cache[safetensors_url])
                if Path(cached_file_path).exists():
                    print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] Using cached file: {cached_file_path}")
                    results.append({
                        "file_name": Path(cached_file_path).name,
                        "strength_model": strength_model,
                        "strength_clip": strength_clip,
                        "original_url": safetensors_url
                    })
                    continue
                else:
                    # キャッシュエントリは存在するがファイルが削除されている場合
                    print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] Cached file not found, re-downloading: {cached_file_path}")
                    del cache[safetensors_url]

            # 一時ファイルを使用してダウンロード
            with tempfile.NamedTemporaryFile(delete=False, suffix=".safetensors") as tmp_file:
                temp_file_path = Path(tmp_file.name)
                try:
                    # ストリーミングダウンロード
                    print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] Downloading: {safetensors_url}")
                    with httpx.stream("GET", safetensors_url) as response:
                        response.raise_for_status()
                        for chunk in response.iter_bytes(chunk_size=8192):
                            tmp_file.write(chunk)

                    tmp_file.flush()

                    # 一時ファイルからバリデーション
                    with open(temp_file_path, "rb") as f:
                        file_data = f.read()

                    if not file_data:
                        print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] ERROR: No file data retrieved.")
                        continue

                    if not Utils._validate_safetensors_data(file_data):
                        print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] ERROR: Invalid safetensors format.")
                        continue

                    # SHA3-512でハッシュ値を計算してファイル名として使用
                    sha3_hash = hashlib.sha3_512(file_data).hexdigest()
                    file_size = len(file_data)
                    print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] Downloaded file size: {file_size} bytes, SHA3-512: {sha3_hash}")
                    file_name = f"download_{sha3_hash}_{file_size}.safetensors"
                    save_path_obj = Path(path_dir, file_name)

                    if save_path_obj.exists():
                        print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] File already exists at: {save_path_obj}")
                        # キャッシュに保存
                        cache[safetensors_url] = str(save_path_obj)
                        results.append({
                            "file_name": save_path_obj.name,
                            "strength_model": strength_model,
                            "strength_clip": strength_clip,
                            "original_url": safetensors_url
                        })
                        continue

                    save_path_obj.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(temp_file_path), str(save_path_obj))

                    # ダウンロード完了後、キャッシュに保存
                    cache[safetensors_url] = str(save_path_obj)

                    print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] Successfully saved safetensors file to: {save_path_obj}")
                    results.append({
                        "file_name": save_path_obj.name,
                        "strength_model": strength_model,
                        "strength_clip": strength_clip,
                        "original_url": safetensors_url
                    })

                except Exception as ex:
                    print(f"[LoadSafetensorsFromMultipleUrls] URL[{idx}] ERROR: {ex}")
                    import traceback
                    traceback.print_exc()
                finally:
                    # 一時ファイルがまだ存在する場合は削除
                    if temp_file_path.exists():
                        temp_file_path.unlink()

        # 結果をJSON形式で返す
        result_json = json.dumps(results, ensure_ascii=False, indent=2)
        print(f"[LoadSafetensorsFromMultipleUrls] Result: {result_json}")
        return comfy_api_io.NodeOutput(result_json)
