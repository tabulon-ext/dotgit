import os
from dotgit.__main__ import main
from dotgit.git import Git


class TestMain:
    def setup_repo(self, tmp_path, flist):
        home = tmp_path / 'home'
        repo = tmp_path / 'repo'
        os.makedirs(home)
        os.makedirs(repo)
        main(args=['init'], cwd=str(repo))
        with open(repo / 'filelist', 'w') as f:
            f.write(flist)

        return home, repo

    def test_init_home(self, tmp_path, caplog):
        home = tmp_path / 'home'
        repo = tmp_path / 'repo'
        os.makedirs(home)
        os.makedirs(repo)

        assert main(args=['init'], cwd=str(home), home=str(home)) != 0
        assert 'safety checks failed' in caplog.text

    def test_init(self, tmp_path, caplog):
        home = tmp_path / 'home'
        repo = tmp_path / 'repo'
        os.makedirs(home)
        os.makedirs(repo)

        assert main(args=['init'], cwd=str(repo), home=str(home)) == 0
        git = Git(str(repo))

        assert (repo / '.git').is_dir()
        assert (repo / 'filelist').is_file()
        assert git.last_commit() == 'Added filelist'

        assert 'existing git repo' not in caplog.text
        assert 'existing filelist' not in caplog.text

    def test_reinit(self, tmp_path, caplog):
        home = tmp_path / 'home'
        repo = tmp_path / 'repo'
        os.makedirs(home)
        os.makedirs(repo)

        assert main(args=['init'], cwd=str(repo), home=str(home)) == 0
        assert main(args=['init'], cwd=str(repo), home=str(home)) == 0
        git = Git(str(repo))

        assert (repo / '.git').is_dir()
        assert (repo / 'filelist').is_file()
        assert git.last_commit() == 'Added filelist'
        assert len(git.commits()) == 1

        assert 'existing git repo' in caplog.text
        assert 'existing filelist' in caplog.text

    def test_update_home_norepo(self, tmp_path):
        home, repo = self.setup_repo(tmp_path, 'file')
        open(home / 'file', 'w').close()

        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0
        assert (home / 'file').is_symlink()
        assert repo in (home / 'file').resolve().parents

    def test_update_home_repo(self, tmp_path, monkeypatch):
        home, repo = self.setup_repo(tmp_path, 'file')
        open(home / 'file', 'w').close()

        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0

        monkeypatch.setattr('builtins.input', lambda p: '0')

        os.remove(home / 'file')
        open(home / 'file', 'w').close()

        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0

        assert (home / 'file').is_symlink()
        assert repo in (home / 'file').resolve().parents

    def test_restore_nohome_repo(self, tmp_path):
        home, repo = self.setup_repo(tmp_path, 'file')
        open(home / 'file', 'w').close()

        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0
        assert (home / 'file').is_symlink()
        assert repo in (home / 'file').resolve().parents

        os.remove(home / 'file')
        assert main(args=['restore'], cwd=str(repo), home=str(home)) == 0
        assert (home / 'file').is_symlink()
        assert repo in (home / 'file').resolve().parents

    def test_restore_home_repo(self, tmp_path, monkeypatch):
        home, repo = self.setup_repo(tmp_path, 'file')
        open(home / 'file', 'w').close()

        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0

        monkeypatch.setattr('builtins.input', lambda p: 'y')

        os.remove(home / 'file')
        open(home / 'file', 'w').close()

        assert main(args=['restore'], cwd=str(repo), home=str(home)) == 0

        assert (home / 'file').is_symlink()
        assert repo in (home / 'file').resolve().parents

    def test_restore_hard_nohome_repo(self, tmp_path):
        home, repo = self.setup_repo(tmp_path, 'file')
        data = 'test data'
        with open(home / 'file', 'w') as f:
            f.write(data)

        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0
        assert (home / 'file').is_symlink()
        assert repo in (home / 'file').resolve().parents

        os.remove(home / 'file')
        assert not (home / 'file').exists()
        assert main(args=['restore', '--hard'],
                    cwd=str(repo), home=str(home)) == 0
        assert (home / 'file').exists()
        assert not (home / 'file').is_symlink()
        assert (home / 'file').read_text() == data

    def test_clean(self, tmp_path):
        home, repo = self.setup_repo(tmp_path, 'file')
        open(home / 'file', 'w').close()

        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0
        assert (home / 'file').is_symlink()
        assert repo in (home / 'file').resolve().parents

        assert main(args=['clean'], cwd=str(repo), home=str(home)) == 0
        assert not (home / 'file').exists()

    def test_dry_run(self, tmp_path):
        home, repo = self.setup_repo(tmp_path, 'file')
        open(home / 'file', 'w').close()

        assert main(args=['update', '--dry-run'],
                    cwd=str(repo), home=str(home)) == 0
        assert (home / 'file').exists()
        assert not (home / 'file').is_symlink()

    def test_commit_nochanges(self, tmp_path, caplog):
        home, repo = self.setup_repo(tmp_path, '')
        assert main(args=['commit'], cwd=str(repo), home=str(home)) == 0
        assert 'no changes detected' in caplog.text

    def test_commit_changes(self, tmp_path, caplog):
        home, repo = self.setup_repo(tmp_path, 'file')
        git = Git(str(repo))
        open(home / 'file', 'w').close()
        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0
        assert main(args=['commit'], cwd=str(repo), home=str(home)) == 0
        assert 'not changes detected' not in caplog.text
        assert 'filelist' in git.last_commit()

    def test_commit_ignore(self, tmp_path, caplog):
        home, repo = self.setup_repo(tmp_path, 'file')
        git = Git(str(repo))
        open(home / 'file', 'w').close()
        os.makedirs(repo / '.plugins')
        open(repo / '.plugins' / 'plugf', 'w').close()

        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0
        assert main(args=['commit'], cwd=str(repo), home=str(home)) == 0
        assert 'not changes detected' not in caplog.text
        assert 'filelist' in git.last_commit()
        assert 'plugf' not in git.last_commit()

    def test_diff(self, tmp_path, capsys):
        home, repo = self.setup_repo(tmp_path, 'file\nfile2')
        (home / 'file').touch()
        (home / 'file2').touch()

        ret = main(args=['update', '--hard'], cwd=str(repo), home=str(home))
        assert ret == 0

        (home / 'file').write_text('hello world')

        ret = main(args=['diff', '--hard'], cwd=str(repo), home=str(home))
        assert ret == 0

        captured = capsys.readouterr()
        assert captured.out == ('added dotfiles/plain/common/file\n'
                                'added dotfiles/plain/common/file2\n'
                                'modified filelist\n\n'
                                'plain-plugin updates not yet in repo:\n'
                                f'modified {home / "file"}\n')

    def test_passwd_empty(self, tmp_path, monkeypatch):
        home, repo = self.setup_repo(tmp_path, 'file\nfile2')

        password = 'password123'
        monkeypatch.setattr('getpass.getpass', lambda prompt: password)

        assert not (repo / '.plugins' / 'encrypt' / 'passwd').exists()
        assert main(args=['passwd'], cwd=str(repo), home=str(home)) == 0
        assert (repo / '.plugins' / 'encrypt' / 'passwd').exists()

    def test_passwd_nonempty(self, tmp_path, monkeypatch):
        home, repo = self.setup_repo(tmp_path, 'file|encrypt')

        password = 'password123'
        monkeypatch.setattr('getpass.getpass', lambda prompt: password)

        (home / 'file').touch()
        assert main(args=['update'], cwd=str(repo), home=str(home)) == 0

        repo_file = repo / 'dotfiles' / 'encrypt' / 'common' / 'file'
        txt = repo_file.read_text()

        assert main(args=['passwd'], cwd=str(repo), home=str(home)) == 0
        assert repo_file.read_text() != txt
