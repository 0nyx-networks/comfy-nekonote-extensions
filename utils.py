import io
import json
import struct
import numpy as np
import tomllib
from pathlib import Path

from PIL import Image
from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]
import torch # pyright: ignore[reportMissingImports]

class Utils:
    @classmethod
    def get_version(cls) -> str:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as fp:
            data = tomllib.load(fp)
        return data["project"]["version"]

    @classmethod
    def tensor_to_image(cls, image: torch.Tensor) -> Image.Image:
        arr = image.detach().cpu().numpy()

        # 余分な次元を削除
        while arr.ndim > 3:
            arr = arr[0]

        arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)

        if arr.shape[-1] == 1:
            arr = arr[:, :, 0]
        elif arr.shape[-1] not in (3, 4):
            raise ValueError(f"Unsupported channel count: {arr.shape}")

        img = Image.fromarray(arr)
        return img

    @classmethod
    def tensor_to_image_bytes(cls, image: torch.Tensor, file_format: str) -> bytes:
        img = cls.tensor_to_image(image)

        buf = io.BytesIO()
        if file_format.lower() == "png":
            img.save(buf, format="PNG")

        elif file_format.lower() == "webp":
            img.save(buf, format="WEBP", optimize=True, lossless=True)

        else:
            raise ValueError("Unsupported format")

        return buf.getvalue()

    @classmethod
    def create_fallback_image(cls, width: int = 1024, height: int = 1024) -> comfy_api_io.NodeOutput:
        """空白イメージを生成"""
        blank_img = Image.new("RGBA", (width, height), color=(255, 255, 255, 255))
        img_array = np.array(blank_img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array).unsqueeze(0)
        return comfy_api_io.NodeOutput(img_tensor, width, height)


    @classmethod
    def _validate_safetensors_data(cls, file_data: bytes) -> bool:
        """
        safetensors形式のバリデーション

        safetensorsファイル構造：
        - 最初の8バイト：ヘッダーサイズ（Little Endian uint64）
        - その後：ヘッダー（JSON形式）
        - その後：実際の重みデータ
        """
        try:
            # ファイルサイズは最低でも8バイト必要
            if len(file_data) < 8:
                print(f"Validation: File too small (< 8 bytes)")
                return False

            # 最初の8バイトからヘッダーサイズをパース（Little Endian）
            header_size = struct.unpack("<Q", file_data[:8])[0]

            # ヘッダーサイズが論理的か確認
            # ヘッダーサイズは大きすぎないはず（例：100MB以上はありえない）
            if header_size > 100_000_000:  # 100MB
                print(f"Validation: Header size too large ({header_size})")
                return False

            # ファイルにヘッダーが完全に収まっているか確認
            if len(file_data) < 8 + header_size:
                print(f"Validation: File too small for header (size: {len(file_data)}, expected: {8 + header_size})")
                return False

            # ヘッダー部分を抽出
            header_bytes = file_data[8:8 + header_size]

            # ヘッダーをJSONとしてパースできるか試す
            header_json = json.loads(header_bytes.decode("utf-8"))

            # ヘッダーが辞書型か確認
            if not isinstance(header_json, dict):
                print(f"Validation: Header is not a valid dictionary")
                return False

            print(f"Validation: Valid safetensors format detected")
            return True

        except struct.error as e:
            print(f"Validation: Invalid struct format - {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"Validation: Invalid JSON header - {e}")
            return False
        except UnicodeDecodeError as e:
            print(f"Validation: Invalid UTF-8 in header - {e}")
            return False
        except Exception as e:
            print(f"Validation: Unexpected error - {e}")
            return False
