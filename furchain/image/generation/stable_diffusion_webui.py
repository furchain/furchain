import tempfile
from typing import Optional

from langchain_core.runnables import RunnableConfig
from webuiapi import WebUIApi

from furchain.config import ImageConfig
from furchain.image.schema import ImageGeneration


class StableDiffusionWebui(ImageGeneration):
    def __init__(self, api_base=None, **kwargs):
        super().__init__()
        if not api_base:
            api_base = ImageConfig.get_stable_diffusion_webui_api_base() + "/sdapi/v1"

        self.webui = WebUIApi(baseurl=api_base)
        self.kwargs = kwargs
        self.webui.set_options(kwargs)

    def invoke(self, input: str | dict, config: Optional[RunnableConfig] = None) -> str:
        if not isinstance(input, dict):
            input = {"prompt": input}
        result = self.webui.txt2img(**input)
        path = tempfile.mktemp(suffix=".png")
        result.image.save(path)
        return path
