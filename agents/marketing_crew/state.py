
class MarketingState(BaseModel):
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    error_count: int = Field(default=0)
    last_error: str = Field(default=None)
    progress: float = Field(default=0.0)
    content_drafts: str = Field(default="")
    social_media_posts: str = Field(default="")
    final_content: str = Field(default="")
