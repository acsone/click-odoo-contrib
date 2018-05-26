# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import subprocess


def commit_if_needed(paths, message, cwd='.'):
    cmd = ['git', 'add'] + paths
    subprocess.check_call(cmd, cwd=cwd)
    cmd = ['git', 'diff', '--quiet', '--exit-code', '--cached', '--'] + paths
    r = subprocess.call(cmd, cwd=cwd)
    if r != 0:
        cmd = ['git', 'commit', '-m', message, '--'] + paths
        subprocess.check_call(cmd, cwd=cwd)
        return True
    else:
        return False
