import io
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
