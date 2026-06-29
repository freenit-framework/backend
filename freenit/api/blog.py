from datetime import datetime
from html import escape

import pydantic
from fastapi import Depends, Header, HTTPException, Request, Response

from freenit.api.router import route
from freenit.decorators import description
from freenit.models.blog import BlogPost, BlogPostOptional, BlogPostTag, NotFoundError, Tag
from freenit.models.pagination import Page, paginate
from freenit.models.user import User
from freenit.permissions import blog_perms

tags = ["blog"]


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class BlogPostCreate(pydantic.BaseModel):
    title: str
    slug: str
    content: str
    date: datetime | None = None
    published: bool = False
    tags: list[str] = []


class BlogPostUpdate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    title: str | None = None
    slug: str | None = None
    content: str | None = None
    date: datetime | None = None
    published: bool | None = None
    tags: list[str] | None = None


class BlogPostResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    content: str
    date: datetime | None = None
    published: bool
    author_id: int | None = None
    tags: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PublicBlogPostResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    content: str
    date: datetime | None = None
    author_id: int | None = None
    tags: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TagResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    name: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_post(id: int) -> BlogPost:
    try:
        return await BlogPost.objects.get(id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such blog post")


async def _get_post_by_slug(slug: str) -> BlogPost:
    try:
        return await BlogPost.objects.filter(slug=slug).get()
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such blog post")


async def _get_tag(name: str) -> Tag:
    try:
        return await Tag.objects.filter(name=name).get()
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such tag")


async def _check_slug_unique(slug: str, exclude_id: int | None = None) -> None:
    existing = await BlogPost.objects.filter(slug=slug).all()
    if any(item.id != exclude_id for item in existing):
        raise HTTPException(status_code=409, detail="Blog post slug already exists")


async def _set_post_tags(post: BlogPost, tag_names: list[str]) -> None:
    existing = await BlogPostTag.objects.filter(post_id=post.id).all()
    for link in existing:
        await link.delete()

    tag_objects = []
    for name in set(tag_names):
        name = name.strip().lower()
        if not name:
            continue
        try:
            tag = await Tag.objects.filter(name=name).get()
        except NotFoundError:
            tag = await Tag.objects.create(name=name)
        tag_objects.append(tag)

    for tag in tag_objects:
        try:
            await BlogPostTag.objects.create(post_id=post.id, tag_id=tag.id)
        except IntegrityError:
            pass


async def _get_post_tags(post_id: int) -> list[str]:
    links = await BlogPostTag.objects.filter(post_id=post_id).all()
    if not links:
        return []
    tag_ids = [link.tag_id for link in links]
    tag_objects = await Tag.objects.filter(id__in=tag_ids).all()
    return sorted(tag.name for tag in tag_objects)


def _post_response(post: BlogPost, tag_names: list[str] | None = None) -> BlogPostResponse:
    if tag_names is None:
        # Tags should be populated before calling; this is a synchronous helper.
        tag_names = []
    data = BlogPostResponse.model_validate(post).model_dump()
    data["tags"] = tag_names
    return BlogPostResponse(**data)


async def _enforce_author_or_admin(post: BlogPost, user: User) -> None:
    if not user.admin and post.author_id != user.id:
        raise HTTPException(
            status_code=403, detail="Only the author or admin can modify this post"
        )


def _rfc822_date(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.strftime("%a, %d %b %Y %H:%M:%S GMT")


# ---------------------------------------------------------------------------
# Admin blog posts
# ---------------------------------------------------------------------------


@route("/blog", tags=tags)
class BlogPostListAPI:
    @staticmethod
    @description("Get blog posts")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(blog_perms),
    ) -> Page[BlogPostResponse]:
        result = await paginate(BlogPost.objects.order_by("-date"), page, perpage)
        for item in result.data:
            tag_names = await _get_post_tags(item.id)
            object.__setattr__(item, "tags", tag_names)
        return result

    @staticmethod
    @description("Create blog post")
    async def post(
        data: BlogPostCreate,
        user: User = Depends(blog_perms),
    ) -> BlogPostResponse:
        await _check_slug_unique(data.slug)
        now = datetime.utcnow()
        post_date = data.date or now
        post = await BlogPost.objects.create(
            title=data.title,
            slug=data.slug,
            content=data.content,
            date=post_date,
            published=data.published,
            author_id=user.id,
            created_at=now,
            updated_at=now,
        )
        await _set_post_tags(post, data.tags)
        tag_names = await _get_post_tags(post.id)
        return _post_response(post, tag_names)


# ---------------------------------------------------------------------------
# Public blog posts
# ---------------------------------------------------------------------------


@route("/blog/public", tags=tags)
class BlogPostPublicListAPI:
    @staticmethod
    @description("Get published blog posts")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
    ) -> Page[PublicBlogPostResponse]:
        query = BlogPost.objects.filter(published=True).order_by("-date")
        result = await paginate(query, page, perpage)
        for item in result.data:
            tag_names = await _get_post_tags(item.id)
            object.__setattr__(item, "tags", tag_names)
        return result


@route("/blog/public/{slug}", tags=tags)
class BlogPostPublicDetailAPI:
    @staticmethod
    @description("Get published blog post")
    async def get(slug: str) -> PublicBlogPostResponse:
        post = await _get_post_by_slug(slug)
        if not post.published:
            raise HTTPException(status_code=404, detail="No such blog post")
        tag_names = await _get_post_tags(post.id)
        object.__setattr__(post, "tags", tag_names)
        return PublicBlogPostResponse.model_validate(post)


@route("/blog/tags", tags=tags)
class BlogTagListAPI:
    @staticmethod
    @description("Get blog tags")
    async def get() -> list[TagResponse]:
        return await Tag.objects.order_by("name").all()


@route("/blog/tags/{name}/posts", tags=tags)
class BlogTagPostsAPI:
    @staticmethod
    @description("Get published blog posts by tag")
    async def get(
        name: str,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
    ) -> Page[PublicBlogPostResponse]:
        tag = await _get_tag(name.lower())
        links = await BlogPostTag.objects.filter(tag_id=tag.id).all()
        post_ids = [link.post_id for link in links]
        if not post_ids:
            return Page(data=[], page=page, perpage=perpage, pages=0, total=0)
        query = BlogPost.objects.filter(id__in=post_ids, published=True).order_by("-date")
        result = await paginate(query, page, perpage)
        for item in result.data:
            tag_names = await _get_post_tags(item.id)
            object.__setattr__(item, "tags", tag_names)
        return result


# ---------------------------------------------------------------------------
# RSS feed
# ---------------------------------------------------------------------------


@route("/blog/rss", tags=tags)
class BlogRssAPI:
    @staticmethod
    @description("Get blog RSS feed")
    async def get(request: Request) -> Response:
        posts = await BlogPost.objects.filter(published=True).order_by("-date").limit(20).all()
        host = request.base_url.netloc
        blog_url = f"{request.base_url.scheme}://{host}/blog"
        now = datetime.utcnow()

        items = []
        for post in posts:
            post_url = f"{blog_url}/{post.slug}"
            tag_names = await _get_post_tags(post.id)
            categories = "".join(
                f"<category>{escape(tag)}</category>" for tag in tag_names
            )
            items.append(
                f"""
    <item>
      <title>{escape(post.title)}</title>
      <link>{escape(post_url)}</link>
      <guid>{escape(post_url)}</guid>
      <pubDate>{_rfc822_date(post.date)}</pubDate>
      {categories}
      <description>{escape(post.content)}</description>
    </item>"""
            )

        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape("Blog")}</title>
    <link>{escape(blog_url)}</link>
    <description>{escape("Latest blog posts")}</description>
    <lastBuildDate>{_rfc822_date(now)}</lastBuildDate>
    {''.join(items)}
  </channel>
</rss>
"""
        return Response(content=rss, media_type="application/rss+xml")


# ---------------------------------------------------------------------------
# Blog post details (must be registered after static /blog/... routes)
# ---------------------------------------------------------------------------


@route("/blog/{id}", tags=tags)
class BlogPostDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(blog_perms)) -> BlogPostResponse:
        post = await _get_post(id)
        tag_names = await _get_post_tags(post.id)
        return _post_response(post, tag_names)

    @staticmethod
    async def patch(
        id: int,
        data: BlogPostUpdate,
        user: User = Depends(blog_perms),
    ) -> BlogPostResponse:
        post = await _get_post(id)
        await _enforce_author_or_admin(post, user)
        if data.slug:
            await _check_slug_unique(data.slug, exclude_id=id)
        update = data.model_dump(exclude_none=True)
        if "tags" in update:
            await _set_post_tags(post, update.pop("tags"))
        if update:
            await post.patch(BlogPostOptional(**update))
        tag_names = await _get_post_tags(post.id)
        return _post_response(post, tag_names)

    @staticmethod
    async def delete(id: int, user: User = Depends(blog_perms)) -> BlogPostResponse:
        post = await _get_post(id)
        await _enforce_author_or_admin(post, user)
        tag_names = await _get_post_tags(post.id)
        response = _post_response(post, tag_names)
        await post.delete()
        return response
