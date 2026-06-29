from __future__ import annotations

from datetime import datetime

import oxyde
import pydantic

from freenit.models.sql.base import OxydeBaseModel, User

NotFoundError = oxyde.NotFoundError
IntegrityError = oxyde.IntegrityError


class Tag(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    name: str = oxyde.Field(db_unique=True, db_index=True)

    class Meta:
        is_table = True
        table_name = "blog_tag"


class BlogPost(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    title: str = oxyde.Field()
    slug: str = oxyde.Field(db_unique=True, db_index=True)
    content: str = oxyde.Field()
    date: datetime | None = oxyde.Field(default=None)
    author: User | None = oxyde.Field(default=None, db_fk="id", db_on_delete="SET NULL")
    published: bool = oxyde.Field(default=False)
    tags: list[Tag] = oxyde.Field(
        default_factory=list, db_m2m=True, db_through="BlogPostTag"
    )
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "blog_post"


class BlogPostTag(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    post: BlogPost | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    tag: Tag | None = oxyde.Field(default=None, db_fk="id", db_on_delete="CASCADE")

    class Meta:
        is_table = True
        table_name = "blog_post_tag"
        unique_together = [("post_id", "tag_id")]


class BlogPostOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    title: str | None = None
    slug: str | None = None
    content: str | None = None
    date: datetime | None = None
    published: bool | None = None
    tags: list[str] | None = None


BlogPost.model_rebuild()
Tag.model_rebuild()
BlogPostTag.model_rebuild()
