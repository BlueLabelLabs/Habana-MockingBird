from __future__ import absolute_import, division, print_function, unicode_literals

import os
import json
import torch
from utils.util import AttrDict
from models.vocoder.hifigan.models import Generator
from utils.util import get_device

generator = None       # type: Generator
output_sample_rate = None     
_device = None


def load_checkpoint(filepath, device):
    assert os.path.isfile(filepath)
    print("Loading '{}'".format(filepath))
    checkpoint_dict = torch.load(filepath, map_location=device)
    print("Complete.")
    return checkpoint_dict


def load_model(weights_fpath, config_fpath=None, verbose=True, device: str = None):
    global generator, _device, output_sample_rate

    if verbose:
        print("Building hifigan")

    if config_fpath == None:
        model_config_fpaths = list(weights_fpath.parent.rglob("*.json"))
        if len(model_config_fpaths) > 0:
            config_fpath = model_config_fpaths[0]
        else:
            config_fpath = "./vocoder/hifigan/config_16k_.json"
    with open(config_fpath) as f:
        data = f.read()
    json_config = json.loads(data)
    h = AttrDict(json_config)
    output_sample_rate = h.sampling_rate
    torch.manual_seed(h.seed)

    _device = torch.device(get_device(device))
    if verbose:
        print("Vocoder using device:", _device)
    generator = Generator(h).to(_device)
    state_dict_g = load_checkpoint(
        weights_fpath, torch.device("cpu")
    )
    generator.load_state_dict(state_dict_g['generator'])
    generator.eval().to(_device)
    generator.remove_weight_norm()


def is_loaded():
    return generator is not None


def infer_waveform(mel, progress_callback=None):

    if generator is None:
        raise Exception("Please load hifi-gan in memory before using it")

    mel = torch.FloatTensor(mel).to(_device)
    mel = mel.unsqueeze(0)

    with torch.no_grad():
        y_g_hat = generator(mel)
        audio = y_g_hat.squeeze()
    audio = audio.cpu().numpy()

    return audio, output_sample_rate

