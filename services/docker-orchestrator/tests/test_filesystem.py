import os

from app.config import settings


def test_browse_filesystem_returns_directories(client, monkeypatch, tmp_path):
    root = tmp_path / "outputs"
    alpha = root / "alpha"
    beta = root / "beta"
    nested = alpha / "nested"
    file_path = root / "ignore.txt"

    nested.mkdir(parents=True)
    beta.mkdir(parents=True)
    file_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(settings, "FILESYSTEM_BROWSE_ROOT", str(root))

    response = client.get("/api/filesystem/browse")

    assert response.status_code == 200
    data = response.json()
    assert data["current_path"] == os.path.realpath(str(root))
    assert data["parent_path"] is None
    assert [entry["name"] for entry in data["entries"]] == ["alpha", "beta"]
    assert data["entries"][0]["children_count"] == 1
    assert data["entries"][1]["children_count"] == 0


def test_browse_filesystem_returns_404_for_missing_directory(client, monkeypatch, tmp_path):
    root = tmp_path / "outputs"
    root.mkdir(parents=True)
    monkeypatch.setattr(settings, "FILESYSTEM_BROWSE_ROOT", str(root))

    response = client.get("/api/filesystem/browse?path=missing-dir")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Directory not found"


def test_browse_filesystem_blocks_path_traversal(client, monkeypatch, tmp_path):
    root = tmp_path / "outputs"
    root.mkdir(parents=True)
    monkeypatch.setattr(settings, "FILESYSTEM_BROWSE_ROOT", str(root))

    response = client.get("/api/filesystem/browse?path=../../etc")

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Path traversal not allowed"


def test_create_directory_returns_created_entry(client, monkeypatch, tmp_path):
    root = tmp_path / "outputs"
    root.mkdir(parents=True)
    monkeypatch.setattr(settings, "FILESYSTEM_BROWSE_ROOT", str(root))

    response = client.post("/api/filesystem/mkdir", json={"path": "new-dir/sub-dir"})

    assert response.status_code == 201
    data = response.json()
    expected_path = os.path.realpath(str(root / "new-dir" / "sub-dir"))
    assert data["name"] == "sub-dir"
    assert data["path"] == expected_path
    assert data["type"] == "directory"
    assert data["children_count"] == 0
    assert os.path.isdir(expected_path)


def test_create_directory_returns_400_for_existing_file(client, monkeypatch, tmp_path):
    root = tmp_path / "outputs"
    root.mkdir(parents=True)
    existing_file = root / "artifact.txt"
    existing_file.write_text("not a dir", encoding="utf-8")
    monkeypatch.setattr(settings, "FILESYSTEM_BROWSE_ROOT", str(root))

    response = client.post("/api/filesystem/mkdir", json={"path": "artifact.txt"})

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Path exists and is not a directory"


def test_create_directory_validation_error(client):
    response = client.post("/api/filesystem/mkdir", json={})
    assert response.status_code == 422
