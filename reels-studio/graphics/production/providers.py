"""Capability registry: only adapters explicitly registered are selectable."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Provider:
    name:str
    capabilities:frozenset[str]
    adapter:object

class Registry:
    def __init__(self): self.providers={}
    def register(self,provider):
        if provider.name in self.providers: raise ValueError('Duplicate provider')
        self.providers[provider.name]=provider
    def require(self,name,capability):
        p=self.providers.get(name)
        if not p or capability not in p.capabilities: raise ValueError(f'Unsupported provider/capability: {name}/{capability}')
        return p.adapter

# Descriptive capabilities are deliberately separate from the legacy Provider API.
# Credentials remain inside each adapter and are never represented here.
from typing import Optional

@dataclass(frozen=True)
class VisualCapabilities:
    identity: str
    model: str
    operations: frozenset[str]
    treatments: frozenset[str]
    input_formats: frozenset[str]
    output_formats: frozenset[str]
    max_width: int
    max_height: int
    max_duration: Optional[float]
    image_to_video: bool
    reference_images: bool
    subject_consistency: str  # none, prompt_only, reference_based
    transparency: bool
    camera_motion: frozenset[str]
    object_motion: bool
    configured: bool
    authorization: str  # authorized, unauthorized, unknown, not_required
    availability: str  # available, unavailable, unknown

    def __post_init__(self):
        if not self.identity or not self.model or self.max_width<1 or self.max_height<1: raise ValueError('Invalid provider profile')
        if self.authorization not in {'authorized','unauthorized','unknown','not_required'} or self.availability not in {'available','unavailable','unknown'}: raise ValueError('Invalid availability status')
        if self.subject_consistency not in {'none','prompt_only','reference_based'}: raise ValueError('Invalid continuity capability')
        if self.subject_consistency=='reference_based' and not self.reference_images: raise ValueError('Reference-based consistency requires reference images')
        if self.image_to_video and 'image_to_video' not in self.operations: raise ValueError('Inconsistent image-to-video capability')
        if self.max_duration is not None and self.max_duration<=0: raise ValueError('Invalid duration limit')

    def status(self,operation):
        if operation not in self.operations:return 'unsupported'
        if not self.configured:return 'unconfigured'
        if self.authorization not in {'authorized','not_required'}:return 'unauthorized' if self.authorization=='unauthorized' else 'authorization_unknown'
        if self.availability!='available':return self.availability
        return 'available'

@dataclass(frozen=True)
class VisualProvider:
    capabilities: VisualCapabilities
    adapter: object

class VisualRegistry:
    def __init__(self): self._providers={}
    def register(self,provider):
        name=provider.capabilities.identity
        if name in self._providers:raise ValueError('Duplicate provider '+name)
        self._providers[name]=provider
    def discover(self,operation):
        return [(name,p.capabilities.status(operation)) for name,p in sorted(self._providers.items())]
    def get(self,name,operation):
        p=self._providers.get(name)
        if p is None:raise ValueError('Provider not configured: '+name)
        status=p.capabilities.status(operation)
        if status!='available':raise ValueError(f'Provider {name} {operation}: {status}')
        if not callable(getattr(p.adapter,'generate',None)):raise ValueError('Provider adapter cannot generate')
        return p
