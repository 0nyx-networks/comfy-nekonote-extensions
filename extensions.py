from comfy_api.latest import ComfyExtension, io as comfy_api_io # pyright: ignore[reportMissingImports]

class ComfyNekonoteExtensions(ComfyExtension):
    async def get_node_list(self) -> list[type[comfy_api_io.ComfyNode]]:
        from .node_calculate_optimize_resolution import CalculateOptimizeResolution
        from .node_convert_csv_to_json import ConvertCsvToJson
        from .node_convert_json_to_yaml import ConvertJsonToYaml
        from .node_convert_yaml_to_json import ConvertYamlToJson
        from .node_csv_list_appender import CsvListAppender
        from .node_display_string_data import DisplayStringData
        from .node_http_request_sender import HttpRequestSender
        from .node_json_value_mutator import JsonValueMutator
        from .node_load_image_from_url import LoadImageFromUrl
        from .node_load_image_info_from_file import LoadImageInfoFromFile
        from .node_load_lora_from_file import LoadLoraFromFile
        from .node_load_lora_from_multiple_files import LoadLoraFromMultipleFiles
        from .node_load_safetensors_from_multiple_urls import LoadSafetensorsFromMultipleUrls
        from .node_load_safetensors_from_url import LoadSafetensorsFromUrl
        from .node_primitive_combo_list import PrimitiveComboList
        from .node_primitive_int_step import PrimitiveIntStep
        from .node_resize_image import ResizeImage

        return [
                    CalculateOptimizeResolution,
                    ConvertCsvToJson,
                    ConvertJsonToYaml,
                    ConvertYamlToJson,
                    CsvListAppender,
                    DisplayStringData,
                    HttpRequestSender,
                    JsonValueMutator,
                    LoadImageFromUrl,
                    LoadImageInfoFromFile,
                    LoadLoraFromFile,
                    LoadLoraFromMultipleFiles,
                    LoadSafetensorsFromMultipleUrls,
                    LoadSafetensorsFromUrl,
                    PrimitiveComboList,
                    PrimitiveIntStep,
                    ResizeImage,
               ]

async def comfy_entrypoint() -> ComfyExtension:
    return ComfyNekonoteExtensions()
