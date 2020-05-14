import os
from pathlib import Path

from dotgit.calc_ops import CalcOps
from dotgit.file_ops import FileOps
from dotgit.plugin_plain import PlainPlugin

class TestCalcOps:
    def setup_home_repo(self, tmp_path):
        os.makedirs(tmp_path / 'home')
        os.makedirs(tmp_path / 'repo')
        return tmp_path/'home', tmp_path/'repo'

    def test_update_no_cands(self, tmp_path, caplog):
        home, repo = self.setup_home_repo(tmp_path)
        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.update({'file': ['cat1', 'cat2']})
        assert 'unable to find any candidates' in caplog.text

    def test_update_master_noslave(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.update({'file': ['cat1', 'cat2']}).apply()

        assert (repo / 'cat1').is_dir()
        assert not (repo / 'cat1' / 'file').is_symlink()
        assert (repo / 'cat2').is_dir()
        assert (repo / 'cat2' / 'file').is_symlink()
        assert (repo / 'cat2' / 'file').samefile(repo / 'cat1' / 'file')

    def test_update_nomaster_slave(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat2')
        open(repo / 'cat2' / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.update({'file': ['cat1', 'cat2']}).apply()

        assert (repo / 'cat1').is_dir()
        assert not (repo / 'cat1' / 'file').is_symlink()
        assert (repo / 'cat2').is_dir()
        assert (repo / 'cat2' / 'file').is_symlink()
        assert (repo / 'cat2' / 'file').samefile(repo / 'cat1' / 'file')

    def test_update_master_linkedslave(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        os.makedirs(repo / 'cat2')
        open(repo / 'cat1' / 'file', 'w').close()
        os.symlink(Path('..') / 'cat1' / 'file', repo / 'cat2' / 'file')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        assert calc.update({'file': ['cat1', 'cat2']}).ops == []

    def test_update_master_brokenlinkslave(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        os.makedirs(repo / 'cat2')
        open(repo / 'cat1' / 'file', 'w').close()
        os.symlink(Path('..') / 'cat1' / 'nonexistent', repo / 'cat2' / 'file')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.update({'file': ['cat1', 'cat2']}).apply()

        assert (repo / 'cat1').is_dir()
        assert not (repo / 'cat1' / 'file').is_symlink()
        assert (repo / 'cat2').is_dir()
        assert (repo / 'cat2' / 'file').is_symlink()
        assert (repo / 'cat2' / 'file').samefile(repo / 'cat1' / 'file')

    def test_update_home_nomaster_noslave(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        open(home / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.update({'file': ['cat1', 'cat2']}).apply()

        assert (repo / 'cat1').is_dir()
        assert not (repo / 'cat1' / 'file').is_symlink()
        assert (repo / 'cat2').is_dir()
        assert (repo / 'cat2' / 'file').is_symlink()
        assert (repo / 'cat2' / 'file').samefile(repo / 'cat1' / 'file')
        assert not (home / 'file').exists()

    def test_update_linkedhome_master_noslave(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        os.symlink(repo / 'cat1' / 'file', home / 'file')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.update({'file': ['cat1', 'cat2']}).apply()

        assert (repo / 'cat1').is_dir()
        assert not (repo / 'cat1' / 'file').is_symlink()
        assert (repo / 'cat2').is_dir()
        assert (repo / 'cat2' / 'file').is_symlink()
        assert (repo / 'cat2' / 'file').samefile(repo / 'cat1' / 'file')
        assert (home / 'file').is_symlink()
        assert (home / 'file').samefile(repo / 'cat1' / 'file')

    def test_update_changed_master(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat2')
        os.makedirs(repo / 'cat3')
        open(repo / 'cat2' / 'file', 'w').close()
        os.symlink(Path('..') / 'cat2' / 'file', repo / 'cat3' / 'file')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.update({'file': ['cat1', 'cat2', 'cat3']}).apply()

        assert (repo / 'cat1').is_dir()
        assert not (repo / 'cat1' / 'file').is_symlink()
        assert (repo / 'cat2').is_dir()
        assert (repo / 'cat2' / 'file').is_symlink()
        assert (repo / 'cat2' / 'file').samefile(repo / 'cat1' / 'file')
        assert (repo / 'cat3').is_dir()
        assert (repo / 'cat3' / 'file').is_symlink()
        assert (repo / 'cat3' / 'file').samefile(repo / 'cat1' / 'file')

    def test_restore_nomaster_nohome(self, tmp_path, caplog):
        home, repo = self.setup_home_repo(tmp_path)

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.restore({'file': ['cat1', 'cat2']}).apply()

        assert 'unable to find "file" in repo, skipping' in caplog.text
        assert not (home / 'file').is_file()

    def test_restore_nomaster_home(self, tmp_path, caplog):
        home, repo = self.setup_home_repo(tmp_path)
        open(home / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.restore({'file': ['cat1', 'cat2']}).apply()

        assert 'unable to find "file" in repo, skipping' in caplog.text
        assert (home / 'file').is_file()

    def test_restore_master_nohome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.restore({'file': ['cat1', 'cat2']}).apply()

        assert (home / 'file').is_file()
        assert (home / 'file').is_symlink()
        assert (home / 'file').samefile(repo / 'cat1' / 'file')
        assert not (repo / 'cat1' / 'file').is_symlink()

    def test_restore_master_linkedhome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        os.symlink(repo / 'cat1' / 'file', home / 'file')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        fops = calc.restore({'file': ['cat1', 'cat2']})
        assert fops.ops == []

    def test_restore_master_home_replace(self, tmp_path, monkeypatch):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        open(home / 'file', 'w').close()

        monkeypatch.setattr('builtins.input', lambda p: 'y')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.restore({'file': ['cat1', 'cat2']}).apply()

        assert (home / 'file').is_file()
        assert (home / 'file').is_symlink()
        assert (home / 'file').samefile(repo / 'cat1' / 'file')
        assert not (repo / 'cat1' / 'file').is_symlink()

    def test_restore_master_home_noreplace(self, tmp_path, monkeypatch):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        open(home / 'file', 'w').close()

        monkeypatch.setattr('builtins.input', lambda p: 'n')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.restore({'file': ['cat1', 'cat2']}).apply()

        assert (home / 'file').is_file()
        assert not (home / 'file').is_symlink()
        assert (repo / 'cat1' / 'file').is_file()
        assert not (repo / 'cat1' / 'file').is_symlink()

    def test_clean_nohome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.clean({'file': ['cat1', 'cat2']}).apply()

        assert not (home / 'file').is_file()
        assert (repo / 'cat1' / 'file').is_file()

    def test_clean_linkedhome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        os.symlink(repo / 'cat1' / 'file', home / 'file')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.clean({'file': ['cat1', 'cat2']}).apply()

        assert not (home / 'file').is_file()
        assert (repo / 'cat1' / 'file').is_file()

    def test_clean_linkedotherhome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        os.symlink(Path('cat1') / 'file', home / 'file')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.clean({'file': ['cat1', 'cat2']}).apply()

        assert (home / 'file').is_symlink()
        assert (repo / 'cat1' / 'file').is_file()

    def test_clean_filehome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        open(home / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.clean({'file': ['cat1', 'cat2']}).apply()

        assert (home / 'file').is_file()
        assert not (home / 'file').is_symlink()
        assert (repo / 'cat1' / 'file').is_file()

    def test_clean_hard_nohome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.clean({'file': ['cat1', 'cat2']}, hard=True).apply()

        assert not (home / 'file').is_file()
        assert (repo / 'cat1' / 'file').is_file()

    def test_clean_hard_linkedhome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        os.symlink(repo / 'cat1' / 'file', home / 'file')

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.clean({'file': ['cat1', 'cat2']}, hard=True).apply()

        assert not (home / 'file').is_file()
        assert (repo / 'cat1' / 'file').is_file()

    def test_clean_hard_filehome(self, tmp_path):
        home, repo = self.setup_home_repo(tmp_path)
        os.makedirs(repo / 'cat1')
        open(repo / 'cat1' / 'file', 'w').close()
        open(home / 'file', 'w').close()

        calc = CalcOps(repo, home, PlainPlugin(tmp_path / '.data'))
        calc.clean({'file': ['cat1', 'cat2']}, hard=True).apply()

        assert not (home / 'file').is_file()
        assert (repo / 'cat1' / 'file').is_file()
