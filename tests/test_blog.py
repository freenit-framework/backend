import pytest

from freenit.models.blog import BlogPostTag

from . import factories


@pytest.mark.asyncio
class TestBlogPost:
    async def test_create_blog_post(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        data = {
            "title": "Hello World",
            "slug": "hello-world",
            "content": "This is a blog post.",
            "published": True,
            "tags": ["news", "update"],
        }
        response = client.post("/blog", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == data["title"]
        assert result["slug"] == data["slug"]
        assert result["content"] == data["content"]
        assert result["published"] is True
        assert result["author_id"] == user.id
        assert sorted(result["tags"]) == ["news", "update"]

    async def test_get_blog_posts(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(author_id=user.id)
        await post.save()
        response = client.get("/blog")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_get_blog_post(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(author_id=user.id)
        await post.save()
        response = client.get(f"/blog/{post.id}")
        assert response.status_code == 200
        assert response.json()["id"] == post.id

    async def test_update_blog_post(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(author_id=user.id)
        await post.save()
        data = {"title": "Updated Title", "tags": ["updated"]}
        response = client.patch(f"/blog/{post.id}", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == data["title"]
        assert result["tags"] == ["updated"]

    async def test_delete_blog_post(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(author_id=user.id)
        await post.save()
        response = client.delete(f"/blog/{post.id}")
        assert response.status_code == 200
        response = client.get(f"/blog/{post.id}")
        assert response.status_code == 404

    async def test_create_blog_post_duplicate_slug(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(slug="unique-slug", author_id=user.id)
        await post.save()
        response = client.post(
            "/blog",
            data={
                "title": "Another",
                "slug": "unique-slug",
                "content": "content",
            },
        )
        assert response.status_code == 409

    async def test_non_author_cannot_edit_blog_post(self, client):
        author = factories.User()
        await author.save()
        other = factories.User()
        await other.save()
        post = factories.BlogPostFactory(author_id=author.id)
        await post.save()
        client.login(user=other)
        response = client.patch(f"/blog/{post.id}", data={"title": "Hacked"})
        assert response.status_code == 403

    async def test_public_blog_post_list(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(published=True, author_id=user.id)
        await post.save()
        client.cookies.clear()
        response = client.get("/blog/public")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_public_blog_post_detail(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(
            slug="public-post", published=True, author_id=user.id
        )
        await post.save()
        client.cookies.clear()
        response = client.get("/blog/public/public-post")
        assert response.status_code == 200
        assert response.json()["slug"] == "public-post"

    async def test_public_blog_post_detail_unpublished(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(
            slug="draft-post", published=False, author_id=user.id
        )
        await post.save()
        client.cookies.clear()
        response = client.get("/blog/public/draft-post")
        assert response.status_code == 404

    async def test_blog_tags_list(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        tag = factories.TagFactory(name="python")
        await tag.save()
        response = client.get("/blog/tags")
        assert response.status_code == 200
        assert any(item["name"] == "python" for item in response.json())

    async def test_blog_posts_by_tag(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(published=True, author_id=user.id)
        await post.save()
        tag = factories.TagFactory(name="python")
        await tag.save()
        link = BlogPostTag(post_id=post.id, tag_id=tag.id)
        await link.save()
        client.cookies.clear()
        response = client.get("/blog/tags/python/posts")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_blog_rss(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        post = factories.BlogPostFactory(
            title="RSS Post", slug="rss-post", published=True, author_id=user.id
        )
        await post.save()
        client.cookies.clear()
        response = client.get("/blog/rss")
        assert response.status_code == 200
        assert "application/rss+xml" in response.headers["content-type"]
        assert "<rss version=\"2.0\">" in response.text
        assert "RSS Post" in response.text
