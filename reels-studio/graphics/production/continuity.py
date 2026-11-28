"""Continuity intent and actual reference linkage, not a guarantee of similarity."""
from dataclasses import dataclass,asdict

@dataclass(frozen=True)
class Continuity:
    subject_id:str
    subject_description:str
    environment:str
    lighting:str
    palette:str
    camera_language:str
    reference_asset_ids:tuple[str,...]=()
    def __post_init__(self):
        if any(not isinstance(x,str) or not x.strip() for x in (self.subject_id,self.subject_description,self.environment,self.lighting,self.palette,self.camera_language)):raise ValueError('Continuity fields required')
        if not all(isinstance(x,str) and x for x in self.reference_asset_ids):raise ValueError('Invalid references')
    def to_dict(self):return asdict(self)
