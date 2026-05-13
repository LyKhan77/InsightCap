import torch


def detect_device() -> str:
    """Return the best available device: 'mps', 'cuda', or 'cpu'."""
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_torch_device() -> torch.device:
    """Return a torch.device for the detected backend."""
    return torch.device(detect_device())
