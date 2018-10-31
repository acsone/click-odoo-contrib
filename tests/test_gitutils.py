# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import subprocess

import pytest

from click_odoo_contrib.gitutils import commit_if_needed


@pytest.fixture
def gitdir(tmpdir):
    subprocess.check_call(["git", "init"], cwd=str(tmpdir))
    subprocess.check_call(["git", "config", "user.name", "tester"], cwd=str(tmpdir))
    subprocess.check_call(
        ["git", "config", "user.email", "tester@example.com"], cwd=str(tmpdir)
    )
    yield tmpdir


def _git_ls_files(cwd):
    output = subprocess.check_output(
        ["git", "ls-files"], cwd=str(cwd), universal_newlines=True
    )
    return output.strip().split("\n")


def _git_staged_files(cwd):
    output = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(cwd),
        universal_newlines=True,
    )
    return output.strip().split("\n")


def _git_add(paths, cwd):
    cmd = ["git", "add", "--"] + paths
    subprocess.check_call(cmd, cwd=str(cwd))


def test_git_commit_if_needed(gitdir):
    assert "file1" not in _git_ls_files(gitdir)
    file1 = gitdir / "file1"
    file1.ensure(file=True)
    assert commit_if_needed([str(file1)], "msg", cwd=str(gitdir))
    assert "file1" in _git_ls_files(gitdir)
    # no change, commit_if_needed returns False
    assert not commit_if_needed([str(file1)], "msg", cwd=str(gitdir))
    # some change
    file1.write("stuff")
    assert commit_if_needed([str(file1)], "msg", cwd=str(gitdir))
    # some unrelated file not in git
    file2 = gitdir / "file2"
    file2.ensure(file=True)
    assert not commit_if_needed([str(file1)], "msg", cwd=str(gitdir))
    assert "file2" not in _git_ls_files(gitdir)
    # some unrelated file in git index
    _git_add([str(file2)], gitdir)
    assert not commit_if_needed([str(file1)], "msg", cwd=str(gitdir))
    assert "file1" not in _git_staged_files(gitdir)
    assert "file2" in _git_staged_files(gitdir)
    # add subdirectory
    dir1 = gitdir / "dir1"
    dir1.ensure(dir=True)
    file3 = dir1 / "file3"
    file3.ensure(file=True)
    assert commit_if_needed([str(file3)], "msg", cwd=str(gitdir))
    assert "dir1/file3" in _git_ls_files(gitdir)


def test_commit_git_ignored(gitdir):
    file1 = gitdir / "file1.pot"
    file1.ensure(file=True)
    gitignore = gitdir / ".gitignore"
    gitignore.write("*.pot\n")
    assert commit_if_needed([str(file1)], "msg", cwd=str(gitdir))
    assert "file1.pot" in _git_ls_files(gitdir)


def test_commit_reldir(gitdir):
    with gitdir.as_cwd():
        os.mkdir("subdir")
        file1 = "subdir/file1"
        with open(file1, "w"):
            pass
        assert commit_if_needed([file1], "msg", cwd="subdir")
