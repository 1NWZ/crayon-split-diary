"""Provider-neutral image-to-video contract. No remote service is connected here."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Protocol, Optional, Tuple
import math

@dataclass(frozen=True)
class Capabilities:
    provider: str
    transport: str  # tool | api | browser | manual
    image_to_video: bool
    accepts_full_collage: bool
    supported_duration_seconds: Tuple[float, ...] = ()  # empty means unknown
    region_control: bool = False
    audio_control: bool = False
    cancellation: bool = False
    verified_from: str = ''  # actual tool metadata, official docs or observed UI

@dataclass(frozen=True)
class VideoRequest:
    request_id: str  # persist and reuse when recovering an unknown submission outcome
    provider: str
    input_image: str  # full collage path; adapter handles authorized transfer
    prompt: str
    requested_duration_seconds: float = 5.0
    top_panel_fraction: float = 0.52
    audio_requested: bool = False
    loop_requested: bool = False
    schema_version: str = '1.0'

    def validate(self):
        if not self.request_id.strip() or not self.provider.strip() or not self.prompt.strip():
            raise ValueError('request_id, provider and prompt are required')
        image = Path(self.input_image)
        if not image.is_file() or image.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
            raise ValueError('input_image must be an existing full-collage image')
        if not math.isfinite(self.requested_duration_seconds) or self.requested_duration_seconds <= 0:
            raise ValueError('requested_duration_seconds must be positive and finite')
        if not math.isfinite(self.top_panel_fraction) or not 0 < self.top_panel_fraction < 1:
            raise ValueError('top_panel_fraction must be between 0 and 1')

    def to_dict(self):
        self.validate()
        return asdict(self)

@dataclass(frozen=True)
class Job:
    request_id: str
    provider: str
    status: str  # not_configured | awaiting_user | queued | running | succeeded | failed | cancelled | unknown
    job_id: Optional[str] = None
    result_locator: Optional[str] = None  # file, provider download reference or URL
    actual_duration_seconds: Optional[float] = None
    error: Optional[str] = None

@dataclass(frozen=True)
class DownloadedVideo:
    path: str
    media_type: str
    provider: str
    job_id: Optional[str]
    # Download success is not visual acceptance. Playback QA is performed separately.

class VideoAdapter(Protocol):
    def capabilities(self) -> Capabilities: ...
    def submit(self, request: VideoRequest) -> Job: ...
    def poll(self, job: Job) -> Job: ...
    def download(self, job: Job, output_directory: Path) -> DownloadedVideo: ...
    def cancel(self, job: Job) -> Job: ...

class UnconfiguredAdapter:
    """Honest default: no guessed endpoint, upload, network call or fake output."""
    def __init__(self, provider: str):
        self.provider = provider

    def capabilities(self) -> Capabilities:
        return Capabilities(self.provider, 'manual', False, False)

    def submit(self, request: VideoRequest) -> Job:
        request.validate()
        if request.provider != self.provider:
            raise ValueError('request provider does not match adapter')
        return Job(request.request_id, self.provider, 'not_configured',
                   error='Connect and verify an image-to-video provider; no request was sent.')

    def poll(self, job: Job) -> Job:
        return job

    def download(self, job: Job, output_directory: Path) -> DownloadedVideo:
        raise RuntimeError('No connected provider or generated video to download')

    def cancel(self, job: Job) -> Job:
        raise RuntimeError('No connected provider job to cancel')
